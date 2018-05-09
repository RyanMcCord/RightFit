import stripe

# def authenticate_stripe():
# 	stripe.api_key = ""
# 	stripe.api_version = '2017-08-15'
	


# def create_bank_account_token():
# 	stripe.Token.create(
# 		bank_account={
# 			"country": 'US',
# 			"currency": 'usd',
# 			"account_holder_name": 'Emma Jackson',
# 			"account_holder_type": 'individual',
# 			"routing_number": '110000000',
# 			"account_number": '000123456789'
# 		},
# 	)

# def stripe_make_charge():
# 	stripe.api_key = "" # get authentication key
# 	stripe.Charge.create(
# 		amount=2000,
# 		currency="usd",
# 		description="<Put in description>",
# 		source="tok_mastercard", # obtained with Stripe.js
# 		idempotency_key='oXTXmt2PwpuGhKyn' # fix this
# 	)


# def create_stripe_account():
# 	stripe.Account.create(
# 		type="standard",
# 		country="US",
# 		email="bob@example.com"
# 	)


# def create_bank_account_for_customer():
# 	token = stripe.Token.create(
# 		bank_account={
# 			"country": 'US',
# 			"currency": 'usd',
# 			"account_holder_name": 'Emma Jackson',
# 			"account_holder_type": 'individual',
# 			"routing_number": '110000000',
# 			"account_number": '000123456789'
# 		},
# 	)
# 	customer = stripe.Customer.retrieve({CUSTOMER_ID})
# 	customer.sources.create(source=token["id"])
	
# def transfer_funds_to_bank():