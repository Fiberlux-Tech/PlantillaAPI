from . import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property

# This file defines the structure of your three database tables using Python classes.
# SQLAlchemy will translate these classes into actual database tables.

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # --- Fields from your definitive list ---
    unidadNegocio = db.Column(db.String(128))
    clientName = db.Column(db.String(128))
    companyID = db.Column(db.String(128))
    salesman = db.Column(db.String(128))
    orderID = db.Column(db.String(128), unique=True)
    tipoCambio = db.Column(db.Float)
    MRC = db.Column(db.Float)
    NRC = db.Column(db.Float)
    VAN = db.Column(db.Float)
    TIR = db.Column(db.Float)
    payback = db.Column(db.Integer)
    totalRevenue = db.Column(db.Float)
    totalExpense = db.Column(db.Float)
    comisiones = db.Column(db.Float)
    comisionesRate = db.Column(db.Float)
    costoInstalacion = db.Column(db.Float)
    costoInstalacionRatio = db.Column(db.Float)
    grossMargin = db.Column(db.Float)
    grossMarginRatio = db.Column(db.Float)
    plazoContrato = db.Column(db.Integer)
    costoCapitalAnual = db.Column(db.Float)
    ApprovalStatus = db.Column(db.String(64), default='PENDING')
    submissionDate = db.Column(db.DateTime, default=datetime.utcnow)
    approvalDate = db.Column(db.DateTime, nullable=True)  # <-- NEW FIELD ADDED HERE

    # --- Relationships to the other tables ---
    # This tells SQLAlchemy that each transaction can have many fixed costs and recurring services.
    fixed_costs = db.relationship('FixedCost', backref='transaction', lazy=True, cascade="all, delete-orphan")
    recurring_services = db.relationship('RecurringService', backref='transaction', lazy=True, cascade="all, delete-orphan")


class FixedCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)

    # --- Fields from your definitive list ---
    categoria = db.Column(db.String(128))
    tipo_servicio = db.Column(db.String(128))
    ticket = db.Column(db.String(128))
    ubicacion = db.Column(db.String(128))
    cantidad = db.Column(db.Float)
    costoUnitario = db.Column(db.Float)
    @hybrid_property
    def total(self):
        """Calculates the total cost dynamically."""
        if self.cantidad is not None and self.costoUnitario is not None:
            return self.cantidad * self.costoUnitario
        return None


class RecurringService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)

    # --- Fields from your definitive list ---
    tipo_servicio = db.Column(db.String(128))
    nota = db.Column(db.String(256))
    ubicacion = db.Column(db.String(128))
    Q = db.Column(db.Float)
    P = db.Column(db.Float)
    CU1 = db.Column(db.Float)
    CU2 = db.Column(db.Float)
    proveedor = db.Column(db.String(128))
    @hybrid_property
    def ingreso(self):
        """Calculates the recurring revenue dynamically."""
        if self.Q is not None and self.P is not None:
            return self.Q * self.P
        return None

    @hybrid_property
    def egreso(self):
        """Calculates the recurring expense dynamically."""
        cu1 = self.CU1 or 0
        cu2 = self.CU2 or 0
        q = self.Q or 0
        return (cu1 + cu2) * q