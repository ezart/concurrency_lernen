import threading

class InsufficientFundsError(Exception):
    pass


class Account:
    _id =0
    def __init__(self, balance:int):
        Account._id += 1
        self.balance = balance
        self.lock = threading.Lock()

   

    @staticmethod
    def transfer(
        from_account: "Account", 
        to_account: "Account", 
        amount: int, 
        barrier: threading.Barrier=None):
        if amount <= 0:
            raise ValueError()
        # get from_account lock 

        if from_account._id == to_account._id :
            raise ValueError("Cannot transfer to the same account")

        first,second = from_account,to_account if from_account._id > to_account._id else to_account,from_account

        with first.lock:
            with second.lock:
                if from_account.balance < amount:
                    raise InsufficientFundsError()
                from_account.balance -= amount
                to_account.balance += amount
        
             

    def get_balance(self):
        with self.lock:
            return self.balance

            

