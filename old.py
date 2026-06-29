# Payment Service - Previous Version
from database import get_db_connection
from enums import PaymentStatus

class PaymentModel:
    """Payment data model"""
    def __init__(self, user_id, amount, status=PaymentStatus.PENDING):
        self.user_id = user_id
        self.amount = amount
        self.status = status
        self.transaction_id = None


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


class PaymentService:
    """Core payment business logic"""

    def __init__(self):
        self.repository = PaymentRepository()

    def process_payment(self, user_id, amount):
        """Process a payment"""
        payment = PaymentModel(user_id, amount)
        self.repository.create_payment(payment)
        return payment

    def get_payment_status(self, payment_id):
        """Get payment status"""
        payment = self.repository.get_payment(payment_id)
        return payment.status if payment else None


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


class PaymentAPI:
    """API router for payment endpoints"""

    def __init__(self):
        self.controller = PaymentController()

    def register_routes(self, app):
        """Register payment routes"""
        app.post('/payments', self.controller.create_payment)
        app.get('/payments/{payment_id}', self.controller.get_payment)
