# CONTEXT_AI.md - PlantillaAPI Financial Transaction Management System

**Purpose**: This document serves as the single source of truth for AI assistants working on this codebase. It explains the project's purpose, architecture, business logic, and development guidelines to ensure consistent, accurate assistance.

---

## 1. Project Purpose & Core Workflow

### The "North Star"
PlantillaAPI is a **financial transaction approval system** designed for sales teams to submit deal evaluations and finance teams to approve/reject them based on profitability metrics. It calculates financial KPIs (NPV, IRR, Payback, Gross Margin) from multi-currency transaction data and enforces business-unit-specific commission rules.

### Primary Data Flow
```
Excel Upload (PLANTILLA.xlsx)
    ↓
Excel Parser (extracts MRC, NRC, fixed costs, recurring services)
    ↓
Financial Calculator (normalizes to PEN, calculates VAN/TIR/Payback/Commission)
    ↓
Database Storage (Transaction + FixedCosts + RecurringServices)
    ↓
KPI Dashboard (role-filtered metrics for PENDING/APPROVED/REJECTED transactions)
```

### Key Actors & Permissions

| Role | View Own | View All | Edit Own PENDING | Edit All PENDING | Approve/Reject | User Management |
|------|----------|----------|------------------|------------------|----------------|-----------------|
| **SALES** | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ |
| **FINANCE** | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| **ADMIN** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Authentication**: Session-based (Flask-Login) with role-based access control (RBAC) enforced via decorators and service-layer filtering.

---

## 2. The Logic "Engine" (Single Source of Truth)

### Main Calculator: `_calculate_financial_metrics()`
**Location**: [app/services/transactions.py:85-301](app/services/transactions.py#L85-L301)

This function is the **single source of truth** for all financial calculations. It performs:

1. **Currency Normalization** (lines 94-140)
   - Converts all monetary values to PEN using locked `tipoCambio`
   - Determines final MRC (user override OR sum of recurring services)

2. **Carta Fianza Calculation** (lines 145-158)
   - Formula: `0.10 × plazo × MRC_ORIG × 1.18 × tasaCartaFianza`
   - Only applies if `aplicaCartaFianza = True`

3. **Revenue Calculation** (line 161)
   - `totalRevenue = NRC_pen + (MRC_pen × plazoContrato)`

4. **Commission Calculation** (line 188)
   - Calls business-unit-specific logic from [commission_rules.py](app/services/commission_rules.py)

5. **Timeline Generation** (lines 191-233)
   - Period-by-period cash flow with distributed fixed costs

6. **NPV/IRR Calculation** (lines 237-279)
   - Uses `numpy-financial` with `costoCapitalAnual`

**Returns**: Dictionary with all KPIs + timeline object

### Business Invariants (NEVER VIOLATE THESE)

#### Invariant #1: All Internal Calculations in PEN
- Every monetary field has 3 variants: `*_original`, `*_currency`, `*_pen`
- Exchange rate (`tipoCambio`) is **locked at transaction submission** and never changes
- All financial metrics (VAN, TIR, Commission, Gross Margin) calculated in PEN
- **Why**: Multi-currency support with consistent calculation base

#### Invariant #2: Commissions Follow Business-Unit-Specific Rules
**Location**: [app/services/commission_rules.py](app/services/commission_rules.py)

- **ESTADO** (lines 4-85): Tiered by profitability, payback, and contract term
- **GIGALAN** (lines 87-169): Region-based rates, payback <2 months required
- **CORPORATIVO** (lines 171-184): Placeholder (6% flat rate)

**Do NOT modify commission logic without understanding the complete decision tree for each business unit.**

#### Invariant #3: APPROVED/REJECTED Transactions Are Immutable
- Once a transaction leaves `PENDING` status, its financial metrics are **frozen**
- Cached in `financial_cache` JSON field (lines 668-695 in transactions.py)
- Prevents historical data modification
- Cache self-heals on read if missing

#### Invariant #4: Exchange Rates Locked at Submission
- `tipoCambio` from `MasterVariable` table is copied to transaction at creation
- Ensures consistent calculations even if master rate changes later
- Same applies to `costoCapitalAnual` and `tasaCartaFianza`

#### Invariant #5: Salesman Field Server-Side Override
**Location**: [app/services/transactions.py:797](app/services/transactions.py#L797)
```python
tx_data['salesman'] = current_user.username  # SECURITY: Prevent spoofing
```
- Frontend-provided `salesman` is **always ignored**
- Server assigns based on authenticated user
- Prevents ownership spoofing

#### Invariant #6: Row-Level Security
- SALES users can only view/edit their own transactions
- Enforced in service layer via query filtering:
  ```python
  if current_user.role == 'SALES':
      query = query.filter(Transaction.salesman == current_user.username)
  ```
- Applied in: transaction retrieval, KPI aggregation, edit operations

---

## 3. Data Architecture Concepts

### Transaction Hierarchy
```
Transaction (parent)
├── FixedCost[] (children, cascade delete)
└── RecurringService[] (children, cascade delete)
```

**Validity Rule**: A transaction MUST have its child records to be valid for financial calculations:
- **FixedCosts**: One-time installation/equipment costs distributed over time
- **RecurringServices**: Monthly revenue and cost streams

**Cascade Behavior**: Deleting a transaction deletes all child records automatically.

### Naming Conventions

#### Excel Cell → Database Field Mapping
**Configuration**: [app/config.py:87-124](app/config.py#L87-L124)

| Excel Cell | Config Key | Database Field | Currency Default |
|------------|-----------|----------------|------------------|
| C2 | clientName | Transaction.clientName | - |
| C10 | MRC | Transaction.MRC_original | PEN |
| C11 | NRC | Transaction.NRC_original | PEN |
| C13 | plazoContrato | Transaction.plazoContrato | - |
| Column N (row 30+) | P | RecurringService.P_original | PEN |
| Column P (row 30+) | CU1 | RecurringService.CU1_original | USD |
| Column F (row 30+) | costoUnitario | FixedCost.costoUnitario_original | USD |

#### Triple-Field Currency Pattern
Every monetary value uses three database fields:
```python
MRC_original    # Value in original currency (user input)
MRC_currency    # Currency code ('PEN' or 'USD')
MRC_pen         # Normalized value in PEN (for calculations)
```

**Normalization Function**: [transactions.py:22-29](app/services/transactions.py#L22-L29)
```python
def _normalize_to_pen(value, currency, exchange_rate):
    if currency == 'USD':
        return value * exchange_rate
    return value
```

#### MRC Override Logic
The system determines final MRC with this priority:
1. **User-provided override** (cell C10): If `MRC_original > 0`, use it
2. **Calculated from services**: Sum of `(P × Q)` for all RecurringServices

### State Machine: Transaction Lifecycle
```
PENDING ──approve()──> APPROVED (immutable, cached)
   │
   └──reject()──> REJECTED (immutable, cached)
```

**State Transition Rules**:
- Only `PENDING` transactions can be edited
- Only `PENDING` transactions can be approved/rejected
- Attempting to approve/reject non-PENDING returns **403 Forbidden**
- Transitions trigger email notifications

**Immutability Enforcement**: [transactions.py:668-695](app/services/transactions.py#L668-L695)
```python
if tx.ApprovalStatus in ['APPROVED', 'REJECTED']:
    if tx.financial_cache:
        return cached_data  # Frozen metrics
    else:
        # Self-healing: recalculate and cache
```

---

## 4. Technical Guardrails

### Security Standards

#### #1: Fail-Fast Configuration Validation
**Location**: [app/config.py:131-222](app/config.py#L131-L222)

```python
Config.validate_config()  # Called at app startup
```

**Critical Variables** (app fails if missing):
- `DATABASE_URL` - PostgreSQL connection string
- `DATAWAREHOUSE_URL` - External master data DB
- `SECRET_KEY` - Flask session encryption (min 32 chars)

**NEVER**:
- Hardcode credentials in code
- Commit `.env` file to version control
- Use weak SECRET_KEY (<32 chars)

#### #2: Row-Level Security via Query Filtering
**Pattern** (from [kpi.py:28-30](app/services/kpi.py#L28-L30)):
```python
if current_user.role == 'SALES':
    query = query.filter(Transaction.salesman == current_user.username)
```

**Applied To**:
- Transaction retrieval
- KPI aggregation
- Edit authorization checks

#### #3: RBAC Decorators
**Location**: [app/utils.py](app/utils.py)

```python
@admin_required          # Only ADMIN role
@finance_admin_required  # FINANCE or ADMIN roles
@login_required          # Any authenticated user
```

**Critical Endpoints**:
- Approve/Reject: `@finance_admin_required`
- User Management: `@admin_required`
- Transaction Edit: Service-layer RBAC (role + ownership check)

### Error Handling Philosophy

#### Service Layer Pattern
**Returns**:
- **Success**: `{"success": True, "data": {...}}`
- **Error**: `({"success": False, "error": "message"}, status_code)` tuple

#### Route Layer Handler
**Function**: `_handle_service_result()` [utils.py:13-29](app/utils.py#L13-L29)

Automatically unpacks service results and converts to JSON responses.

#### Logging Standard
```python
app.logger.error(f"Detailed error message: {str(e)}", exc_info=True)
```

**Use For**:
- Database errors
- External API failures
- Unexpected exceptions

**Avoid**:
- Leaking sensitive data in error messages
- Generic "An error occurred" messages (be specific for debugging)

### Update Patterns

#### "Delete and Recreate" for Child Records
**Location**: [transactions.py:306-444](app/services/transactions.py#L306-L444) - `_update_transaction_data()`

When updating FixedCosts or RecurringServices:
1. **Delete** existing child records
2. **Recreate** from new payload
3. **Recalculate** all financial metrics

**Why**: Simpler than patching, avoids orphaned records, ensures data consistency.

#### Immutability Enforcement
```python
# Check before edit (transactions.py:973-976)
if tx.ApprovalStatus != 'PENDING':
    return {"success": False, "error": "Cannot edit non-PENDING transaction"}, 403
```

---

## 5. AI Interaction Rules ("How to Help Me")

### Communication Style
1. **Conceptual First, Code Second**
   - When asked about implementation, first explain the architectural approach
   - Discuss trade-offs before writing code
   - Example: "There are two ways to handle this: [A] or [B]. A is simpler but less flexible. Which fits your needs?"

2. **Be Specific About Locations**
   - Always reference file paths with line numbers
   - Example: "The issue is in [transactions.py:125](app/services/transactions.py#L125)"

3. **Explain Business Context**
   - Don't just fix code, explain WHY the current behavior exists
   - Example: "This check prevents SALES users from editing other users' transactions (Invariant #6)"

### Code Review Priorities (IN ORDER)

#### Priority 1: Financial Accuracy & Currency Normalization
**Check**:
- Are all calculations using `*_pen` fields?
- Is `tipoCambio` being locked at transaction creation?
- Are `_normalize_to_pen()` calls correct?
- Does commission calculation route to correct business unit?

**Example Bad Code**:
```python
total_revenue = MRC_original * plazo  # WRONG: Mixed currencies!
```

**Example Good Code**:
```python
total_revenue = MRC_pen * plazo  # CORRECT: Normalized to PEN
```

#### Priority 2: Business Invariants Compliance
**Check**:
- Is immutability being preserved (no edits to APPROVED/REJECTED)?
- Is salesman field being overwritten server-side?
- Are row-level security filters applied?
- Are child records being created/updated correctly?

#### Priority 3: Security (RBAC, Input Validation)
**Check**:
- Are decorators applied correctly?
- Is user input being validated?
- Are SQL injection risks mitigated (use ORM, not raw SQL)?
- Is `.env` being used for secrets?

#### Priority 4: Code Syntax & Style
**Check**:
- PEP 8 compliance
- Error handling
- Code duplication
- Performance optimizations

**Note**: Syntax is the LOWEST priority. A syntactically perfect but financially incorrect function is worse than a messy but accurate one.

### Next-Step Proactivity

After solving a problem, ALWAYS suggest the next logical step:

**Examples**:
- "I've fixed the commission calculation. Next, you should test this with GIGALAN transactions (region='PROVINCIAS CON CACHING') to verify the rate tiers."
- "I've added the new field to the model. Next steps: 1) Create a migration, 2) Update the Excel parser to extract this field, 3) Update the frontend form."
- "The bug is fixed. Consider adding a unit test in `tests/test_commission_rules.py` to prevent regression."

### Avoid Over-Engineering

**DO**:
- Make ONLY the requested changes
- Use existing patterns in the codebase
- Solve the immediate problem

**DON'T**:
- Add "nice to have" features unprompted
- Refactor unrelated code
- Create abstractions for one-time operations
- Add extensive documentation to unchanged code

**Example**:
- **Request**: "Fix the typo in the error message"
- **Bad**: Fix typo + refactor error handling + add new validation + update docstrings
- **Good**: Fix the typo only

---

## 6. Quick Reference

### Key Files & Line Numbers

#### Core Business Logic
- **Main Calculator**: [app/services/transactions.py:85-301](app/services/transactions.py#L85-L301) - `_calculate_financial_metrics()`
- **Commission Rules**: [app/services/commission_rules.py](app/services/commission_rules.py)
  - ESTADO: lines 4-85
  - GIGALAN: lines 87-169
  - CORPORATIVO: lines 171-184

#### Data Layer
- **Database Models**: [app/models.py](app/models.py)
  - Transaction: lines 36-146
  - FixedCost: lines 149-184
  - RecurringService: lines 187-242
  - User: lines 9-33
  - MasterVariable: lines 245-297

#### Configuration
- **App Config**: [app/config.py](app/config.py)
  - Excel cell mappings: lines 87-124
  - Fail-fast validation: lines 131-222
- **Environment Variables**: `.env` (never commit!)

#### API Layer
- **Transaction Routes**: [app/api/transactions.py](app/api/transactions.py)
  - Upload: line 34 (POST `/api/process-excel`)
  - Submit: line 68 (POST `/api/submit-transaction`)
  - Approve: line 124 (POST `/api/transaction/approve/<id>`)
  - Reject: line 145 (POST `/api/transaction/reject/<id>`)

#### Auth & RBAC
- **Authentication**: [app/auth.py](app/auth.py)
- **Decorators**: [app/utils.py](app/utils.py)
  - `@admin_required`: lines 33-46
  - `@finance_admin_required`: lines 49-65

### Database Schema Quick Reference

#### Transaction Table
```sql
id (PK, String 128)              -- Format: FLXyy-MMDDHHMMSSFFFFFF
clientName, companyID, salesman
MRC_original, MRC_currency, MRC_pen
NRC_original, NRC_currency, NRC_pen
tipoCambio (locked at creation)
plazoContrato (Integer, months)
VAN, TIR, payback                -- Calculated KPIs
grossMargin, grossMarginRatio
comisiones, comisionesRate
ApprovalStatus                   -- 'PENDING', 'APPROVED', 'REJECTED'
submissionDate, approvalDate
financial_cache (JSON)           -- Cached metrics for immutable transactions
```

#### RecurringService Table (Children)
```sql
id (PK, Integer)
transaction_id (FK → transaction.id)
Q (Quantity), P_pen (Price in PEN), CU1_pen, CU2_pen (Costs in PEN)
tipo_servicio, ubicacion, proveedor
-- Calculated: ingreso_pen = Q × P_pen
-- Calculated: egreso_pen = (CU1_pen + CU2_pen) × Q
```

#### FixedCost Table (Children)
```sql
id (PK, Integer)
transaction_id (FK → transaction.id)
cantidad (Quantity), costoUnitario_pen (Unit cost in PEN)
periodo_inicio (Integer, 0-indexed), duracion_meses (Integer)
categoria, tipo_servicio, ticket, ubicacion
-- Calculated: total_pen = cantidad × costoUnitario_pen
```

### Commission Calculation Decision Tree (Simplified)

#### ESTADO
```
IF plazoContrato ≤ 1:
  Tiered by grossMarginRatio (30-35%: 1%, 35-39%: 2%, ..., >59%: 5%)
ELSE IF plazoContrato = 12:
  Tiered by grossMarginRatio + payback ≤7 (rates: 2.5%-3.5%)
ELSE IF plazoContrato = 24:
  Tiered by grossMarginRatio + payback ≤11 (rates: 2.5%-3.5%)
-- Similar for 36 and 48 months
```

#### GIGALAN
```
IF payback ≥ 2: commission = 0
ELSE:
  IF region = 'LIMA' AND sale_type = 'NUEVO':
    Tiered by grossMarginRatio (40-50%: 0.9%, ..., ≥70%: 2.4%)
  ELSE IF region = 'LIMA' AND sale_type = 'EXISTENTE':
    Tiered by grossMarginRatio using incremental MRC
  -- Similar for PROVINCIAS variants
```

### Common Operation Patterns

#### Adding a New API Endpoint
1. Create route in appropriate blueprint (`app/api/*.py`)
2. Apply RBAC decorator (`@login_required`, `@finance_admin_required`, etc.)
3. Create service function in `app/services/*.py`
4. Return result using `_handle_service_result(result)`

#### Adding a New Database Field
1. Update model in [app/models.py](app/models.py)
2. Create migration: `flask db migrate -m "description"`
3. Apply migration: `flask db upgrade`
4. Update Excel parser if needed ([excel_parser.py](app/services/excel_parser.py))
5. Update calculator if it affects KPIs ([transactions.py](app/services/transactions.py))

#### Adding a New Master Variable
1. Add to `MASTER_VARIABLE_ROLES` in [config.py](app/config.py)
2. Insert seed data via SQL or admin panel
3. Update Excel parser to fetch it ([excel_parser.py:36-44](app/services/excel_parser.py#L36-L44))
4. Lock it at transaction creation ([transactions.py:803-820](app/services/transactions.py#L803-L820))

---

## Final Notes for AI Assistants

**When in Doubt**:
1. Check the business invariants (Section 2) - these are non-negotiable
2. Trace the data flow (Section 1) - understand where data comes from and goes to
3. Review existing patterns - this codebase has established conventions, follow them
4. Ask clarifying questions - don't assume requirements

**Red Flags to Watch For**:
- Mixing `*_original` and `*_pen` fields in calculations
- Editing APPROVED/REJECTED transactions
- Bypassing row-level security filters
- Hardcoding business logic (commission rates, formulas)
- Modifying `salesman` field from frontend

**Remember**: This system handles real financial decisions. Accuracy > Speed. When uncertain about financial logic, ask before implementing.
