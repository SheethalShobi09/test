# Payment Service - New Version with Refunds and Disputes
from database import get_db_connection
from enums import PaymentStatus
from validators import PaymentValidator, RefundValidator
from logger import logger

class PaymentModel:
    """Payment data model"""
    def __init__(self, user_id, amount, status=PaymentStatus.PENDING):
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.transaction_id = None


class RefundModel:
    """Refund data model - NEW"""
    def __init__(self, payment_id, amount, reason):
        self.payment_id = payment_id
        self.amount = amount
        self.reason = reason
        self.status = PaymentStatus.PENDING


class DisputeModel:
    """Dispute data model - NEW"""
    def __init__(self, payment_id, reason, evidence):
        self.payment_id = payment_id
        self.reason = reason
        self.evidence = evidence
        self.status = "OPEN"


class PaymentRepository:
    """Data access layer for payments"""

    def __init__(self):
        self.db = get_db_connection()

    def create_payment(self, payment: PaymentModel):
        query = "INSERT INTO payments (user_id, amount, status) VALUES (%s, %s, %s)"
        return self.db.execute(query, [payment.user_id, payment.amount, payment.status])

    def get_payment(self, payment_id):
        query = "SELECT * FROM payments WHERE id = %s"
        return self.db.fetch_one(query, [payment_id])

    def update_payment_status(self, payment_id, status):
        query = "UPDATE payments SET status = %s WHERE id = %s"
        return self.db.execute(query, [status, payment_id])


class RefundRepository:
    """Data access layer for refunds - NEW"""

    def __init__(self):
        self.db = get_db_connection()

    def create_refund(self, refund: RefundModel):
        query = "INSERT INTO refunds (payment_id, amount, reason, status) VALUES (%s, %s, %s, %s)"
        return self.db.execute(query, [refund.payment_id, refund.amount, refund.reason, refund.status])

    def get_refund(self, refund_id):
        query = "SELECT * FROM refunds WHERE id = %s"
        return self.db.fetch_one(query, [refund_id])

    def get_refunds_by_payment(self, payment_id):
        query = "SELECT * FROM refunds WHERE payment_id = %s"
        return self.db.fetch_all(query, [payment_id])


class DisputeRepository:
    """Data access layer for disputes - NEW"""

    def __init__(self):
        self.db = get_db_connection()

    def create_dispute(self, dispute: DisputeModel):
        query = "INSERT INTO disputes (payment_id, reason, evidence, status) VALUES (%s, %s, %s, %s)"
        return self.db.execute(query, [dispute.payment_id, dispute.reason, dispute.evidence, dispute.status])

    def get_dispute(self, dispute_id):
        query = "SELECT * FROM disputes WHERE id = %s"
        return self.db.fetch_one(query, [dispute_id])


class PaymentService:
    """Core payment business logic"""

    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.validator = PaymentValidator()

    def process_payment(self, user_id, amount):
        """Process a payment"""
        if not self.validator.validate(user_id, amount):
            raise ValueError("Invalid payment data")
        payment = PaymentModel(user_id, amount)
        self.payment_repo.create_payment(payment)
        logger.info(f"Payment created: {payment.id}")
        return payment

    def get_payment_status(self, payment_id):
        """Get payment status"""
        payment = self.payment_repo.get_payment(payment_id)
        return payment.status if payment else None


class RefundService:
    """Refund business logic - NEW"""

    def __init__(self):
        self.refund_repo = RefundRepository()
        self.payment_repo = PaymentRepository()
        self.validator = RefundValidator()

    def create_refund(self, payment_id, amount, reason):
        """Create a refund for a payment"""
        if not self.validator.validate(payment_id, amount, reason):
            raise ValueError("Invalid refund data")

        payment = self.payment_repo.get_payment(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        refund = RefundModel(payment_id, amount, reason)
        self.refund_repo.create_refund(refund)
        logger.info(f"Refund created: {refund.id}")
        return refund

    def get_refund_status(self, refund_id):
        """Get refund status"""
        refund = self.refund_repo.get_refund(refund_id)
        return refund.status if refund else None


class DisputeService:
    """Dispute handling logic - NEW"""

    def __init__(self):
        self.dispute_repo = DisputeRepository()
        self.payment_repo = PaymentRepository()

    def file_dispute(self, payment_id, reason, evidence):
        """File a dispute for a payment"""
        payment = self.payment_repo.get_payment(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        dispute = DisputeModel(payment_id, reason, evidence)
        self.dispute_repo.create_dispute(dispute)
        logger.info(f"Dispute filed: {dispute.id}")
        return dispute

    def resolve_dispute(self, dispute_id, resolution):
        """Resolve a dispute"""
        dispute = self.dispute_repo.get_dispute(dispute_id)
        if not dispute:
            raise ValueError("Dispute not found")
        logger.info(f"Dispute resolved: {dispute_id}")
        return dispute


class PaymentController:
    """HTTP controller for payment endpoints"""

    def __init__(self):
        self.service = PaymentService()

    def create_payment(self, request):
        """POST /payments"""
        user_id = request.get('user_id')
        amount = request.get('amount')
        payment = self.service.process_payment(user_id, amount)
        return {"id": payment.id, "status": payment.status}

    def get_payment(self, request):
        """GET /payments/{payment_id}"""
        payment_id = request.get('payment_id')
        status = self.service.get_payment_status(payment_id)
        return {"status": status}


class RefundController:
    """HTTP controller for refund endpoints - NEW"""

    def __init__(self):
        self.service = RefundService()

    def create_refund(self, request):
        """POST /refunds"""
        payment_id = request.get('payment_id')
        amount = request.get('amount')
        reason = request.get('reason')
        refund = self.service.create_refund(payment_id, amount, reason)
        return {"id": refund.id, "status": refund.status}

    def get_refund(self, request):
        """GET /refunds/{refund_id}"""
        refund_id = request.get('refund_id')
        status = self.service.get_refund_status(refund_id)
        return {"status": status}


class DisputeController:
    """HTTP controller for dispute endpoints - NEW"""

    def __init__(self):
        self.service = DisputeService()

    def file_dispute(self, request):
        """POST /disputes"""
        payment_id = request.get('payment_id')
        reason = request.get('reason')
        evidence = request.get('evidence')
        dispute = self.service.file_dispute(payment_id, reason, evidence)
        return {"id": dispute.id, "status": dispute.status}

    def resolve_dispute(self, request):
        """PATCH /disputes/{dispute_id}"""
        dispute_id = request.get('dispute_id')
        resolution = request.get('resolution')
        dispute = self.service.resolve_dispute(dispute_id, resolution)
        return {"id": dispute.id, "status": dispute.status}


class PaymentAPI:
    """API router for payment endpoints"""

    def __init__(self):
        self.payment_controller = PaymentController()
        self.refund_controller = RefundController()
        self.dispute_controller = DisputeController()

    def register_routes(self, app):
        """Register all payment-related routes"""
        # Payment routes
        app.post('/payments', self.payment_controller.create_payment)
        app.get('/payments/{payment_id}', self.payment_controller.get_payment)

        # Refund routes - NEW
        app.post('/refunds', self.refund_controller.create_refund)
        app.get('/refunds/{refund_id}', self.refund_controller.get_refund)

        # Dispute routes - NEW
        app.post('/disputes', self.dispute_controller.file_dispute)
        app.patch('/disputes/{dispute_id}', self.dispute_controller.resolve_dispute)
