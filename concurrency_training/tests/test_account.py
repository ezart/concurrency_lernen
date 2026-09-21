# from concurrent.futures import ThreadPoolExecutor
# import threading

# import unittest

# from challenges.challenge_01.account import Account
# from challenges.challenge_01.account import InsufficientFundsError

# class TestAccount(unittest.TestCase):
#     def test_basic_transfer(self):
#         account_a = Account(balance=1000)
#         account_b = Account(balance=500)

#         Account.transfer(account_a, account_b, 250)
#         self.assertEqual(account_a.get_balance(),750)
#         self.assertEqual(account_b.get_balance(),750)


#     def test_from_account_insufficient_balance(self):
#         account_a = Account(balance=1000)
#         account_b = Account(balance=500)

#         with self.assertRaises(Exception):
#             Account.transfer(account_a, account_b, 1250)

#     def test_invalid_transfer_amount(self):
#         a = Account(100)
#         b = Account(100)

#         with self.assertRaises(ValueError):
#             Account.transfer(a,b,0)



#     def test_concurrent_transfers(self):
#         a = Account(balance=1000)
#         b = Account(balance=0)
#         c = Account(balance=1000)
#         d = Account(balance=0)


#         def worker_a_to_b():
#             for _ in range(100):
#                 Account.transfer(a,b,10)
#         def worker_c_to_d():
#             for _ in range(100):
#                 Account.transfer(c,d,10)

#         with ThreadPoolExecutor(max_workers=2) as executor:
#             future1 = executor.submit(worker_a_to_b)
#             future2 = executor.submit(worker_c_to_d)

#             # call result to surface any exceptions raised within the threads
#             future1.result()
#             future2.result()


#         self.assertEqual(a.balance, 0)
#         self.assertEqual(b.balance, 1000)
#         self.assertEqual(c.balance, 0)
#         self.assertEqual(d.balance, 1000)

#     def test_opposing_concurrent_transfers(self):
#         a = Account(100)
#         b = Account(100)

#         barrier = threading.Barrier(2)

#         t1 = threading.Thread(target=lambda:Account.transfer(a,b,10,barrier=barrier))
#         t2 = threading.Thread(target=lambda:Account.transfer(b,a,10, barrier=barrier))


#         t1.start()
#         t2.start()


#         # wait for up to 1 second for threads to finish
#         t1.join(timeout=1.0)
#         t2.join(timeout=1.0)

#         self.assertFalse(t1.is_alive(),"thread 1 should be deadlocked")
#         self.assertFalse(t2.is_alive(),"thread 2 ahould be deadlocked")


#     # def test_opposing_concurrent_transfers(self):

#     #     a = Account(balance=1000)
#     #     b = Account(balance=0)
#     #     c = Account(balance=1000)
#     #     d = Account(balance=100)

#     #     def a_2_b():
#     #         for _ in range(100):
#     #             Account.transfer(a,b,10)

#     #     def b_2_a():
#     #         for _ in range(1000):
#     #             Account.transfer(b,a,10)

#     #     def c_2_d():
#     #         for _ in range(100):
#     #             Account.transfer(c,d,10)
#     #     def d_2_c():
#     #         for _ in range(100):
#     #             Account.transfer(d,a,10)




#     #     with ThreadPoolExecutor() as executor:

#     #         with self.assertRaises(InsufficientFundsError):
#     #             future1 = executor.submit(a_2_b)
#     #             future2 = executor.submit(b_2_a)
#     #             future3 = executor.submit(c_2_d)
#     #             future4 = executor.submit(d_2_c)

#     #             future1.result()
#     #             future2.result()
#     #             future3.result()
#     #             future4.result()

#     #     self.assertEqual(a.balance,2000)
#     #     self.assertEqual(b.balance, 0)
#     #     self.assertEqual(c.balance,0)
#     #     self.assertEqual(d.balance,100)





