CREATE TABLE webhook_event_types (
	id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	resource_versions JSON, 
	category VARCHAR(100), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_webhook_event_types_id ON webhook_event_types (id);
CREATE UNIQUE INDEX ix_webhook_event_types_name ON webhook_event_types (name);
CREATE TABLE users (
	id VARCHAR(13) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	email_verified BOOLEAN, 
	username VARCHAR(255), 
	name VARCHAR(255), 
	given_name VARCHAR(255), 
	family_name VARCHAR(255), 
	middle_name VARCHAR(255), 
	picture TEXT, 
	gender VARCHAR(50), 
	birthdate VARCHAR(50), 
	zoneinfo VARCHAR(100), 
	locale VARCHAR(10), 
	phone_number VARCHAR(50), 
	phone_number_verified BOOLEAN, 
	address TEXT, 
	account_type VARCHAR(50), 
	verified_account BOOLEAN, 
	age_range VARCHAR(20), 
	account_status VARCHAR(50), 
	account_creation_date DATETIME, 
	updated_at DATETIME, 
	last_login_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (username)
);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE TABLE web_profiles (
	id VARCHAR(22) NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	"temporary" BOOLEAN, 
	flow_config JSON, 
	input_fields JSON, 
	presentation JSON, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_web_profiles_id ON web_profiles (id);
CREATE INDEX ix_web_profiles_user_id ON web_profiles (user_id);
CREATE TABLE orders (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(50) NOT NULL, 
	status VARCHAR(21) NOT NULL, 
	intent VARCHAR(9) NOT NULL, 
	create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	update_time DATETIME, 
	return_url VARCHAR(2048), 
	cancel_url VARCHAR(2048), 
	brand_name VARCHAR(255), 
	locale VARCHAR(20), 
	landing_page VARCHAR(14), 
	shipping_preference VARCHAR(20), 
	user_action VARCHAR(8), 
	prefer VARCHAR(25), 
	paypal_request_id VARCHAR(108), 
	paypal_partner_attribution_id VARCHAR(36), 
	paypal_client_metadata_id VARCHAR(36), 
	paypal_auth_assertion VARCHAR(2048), 
	payment_source JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_orders_user_id ON orders (user_id);
CREATE INDEX ix_orders_user_id ON orders (user_id);
CREATE INDEX idx_orders_create_time ON orders (create_time);
CREATE INDEX idx_orders_user_status ON orders (user_id, status);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_intent ON orders (intent);
CREATE TABLE subscribers (
	id VARCHAR(50) NOT NULL, 
	email_address VARCHAR(254), 
	user_id VARCHAR(13), 
	name_prefix VARCHAR(140), 
	given_name VARCHAR(140), 
	middle_name VARCHAR(140), 
	surname VARCHAR(140), 
	name_suffix VARCHAR(140), 
	full_name VARCHAR(300), 
	phone_type VARCHAR(6), 
	phone_country_code VARCHAR(3), 
	phone_national_number VARCHAR(14), 
	phone_extension_number VARCHAR(15), 
	address_line_1 VARCHAR(300), 
	address_line_2 VARCHAR(300), 
	admin_area_2 VARCHAR(120), 
	admin_area_1 VARCHAR(300), 
	postal_code VARCHAR(60), 
	country_code VARCHAR(2), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_subscribers_user_id ON subscribers (user_id);
CREATE INDEX ix_subscribers_email_address ON subscribers (email_address);
CREATE TABLE webhook_events (
	id VARCHAR(50) NOT NULL, 
	event_version VARCHAR(10) NOT NULL, 
	create_time DATETIME NOT NULL, 
	resource_type VARCHAR(100), 
	resource_version VARCHAR(10) NOT NULL, 
	event_type VARCHAR(100) NOT NULL, 
	summary TEXT, 
	resource JSON, 
	user_id VARCHAR(13), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_webhook_events_create_time ON webhook_events (create_time);
CREATE INDEX ix_webhook_events_event_type ON webhook_events (event_type);
CREATE INDEX ix_webhook_events_id ON webhook_events (id);
CREATE INDEX ix_webhook_events_user_id ON webhook_events (user_id);
CREATE TABLE webhooks (
	id VARCHAR(50) NOT NULL, 
	url VARCHAR(2048) NOT NULL, 
	user_id VARCHAR(13), 
	status VARCHAR(50) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_webhooks_id ON webhooks (id);
CREATE INDEX ix_webhooks_user_id ON webhooks (user_id);
CREATE TABLE webhook_lookups (
	id VARCHAR(17) NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	url TEXT NOT NULL, 
	app_id VARCHAR(255), 
	status VARCHAR(50) NOT NULL, 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_webhook_lookups_user_id ON webhook_lookups (user_id);
CREATE INDEX idx_webhook_user_url ON webhook_lookups (user_id, url);
CREATE INDEX idx_webhook_user_id ON webhook_lookups (user_id, id);
CREATE TABLE partner_referrals (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	partner_id VARCHAR(100) NOT NULL, 
	tracking_id VARCHAR(127), 
	email VARCHAR(254), 
	preferred_language_code VARCHAR(10), 
	legal_country_code VARCHAR(2), 
	business_entity JSON, 
	individual_owners JSON, 
	operations JSON NOT NULL, 
	products JSON, 
	capabilities JSON, 
	legal_consents JSON NOT NULL, 
	partner_config JSON, 
	financial_instruments JSON, 
	payout_attributes JSON, 
	outside_process_dependencies JSON, 
	status VARCHAR(11) NOT NULL, 
	action_url TEXT, 
	action_url_expiry DATETIME, 
	return_url TEXT, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_partner_referrals_id ON partner_referrals (id);
CREATE INDEX ix_partner_referrals_user_id ON partner_referrals (user_id);
CREATE INDEX ix_partner_referrals_partner_id ON partner_referrals (partner_id);
CREATE INDEX ix_partner_referrals_tracking_id ON partner_referrals (tracking_id);
CREATE TABLE products (
	id VARCHAR(50) NOT NULL, 
	name VARCHAR(127) NOT NULL, 
	description VARCHAR(256), 
	type VARCHAR(8) NOT NULL, 
	category VARCHAR(256), 
	image_url VARCHAR(2000), 
	home_url VARCHAR(2000), 
	user_id VARCHAR(13) NOT NULL, 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_product_category ON products (category);
CREATE INDEX idx_product_create_time ON products (create_time);
CREATE INDEX idx_product_type ON products (type);
CREATE INDEX ix_products_name ON products (name);
CREATE INDEX ix_products_user_id ON products (user_id);
CREATE INDEX ix_products_category ON products (category);
CREATE TABLE disputes (
	dispute_id VARCHAR(50) NOT NULL, 
	id VARCHAR(50), 
	disputed_transaction_id VARCHAR(50), 
	create_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
	update_time DATETIME, 
	reason VARCHAR(39) NOT NULL, 
	status VARCHAR(27) NOT NULL, 
	dispute_state VARCHAR(27), 
	dispute_life_cycle_stage VARCHAR(15), 
	dispute_channel VARCHAR(24), 
	dispute_amount_value NUMERIC(19, 6) NOT NULL, 
	dispute_amount_currency VARCHAR(3) NOT NULL, 
	buyer_transaction_id VARCHAR(50), 
	seller_transaction_id VARCHAR(50), 
	buyer_email VARCHAR(255), 
	buyer_name VARCHAR(255), 
	seller_email VARCHAR(255), 
	seller_name VARCHAR(255), 
	buyer_message TEXT, 
	seller_response TEXT, 
	evidence_documents JSON, 
	seller_response_due_date DATETIME, 
	buyer_response_due_date DATETIME, 
	resolved_time DATETIME, 
	user_id VARCHAR(13) NOT NULL, 
	external_id VARCHAR(50), 
	notes TEXT, 
	partner_actions JSON, 
	communication_detail JSON, 
	PRIMARY KEY (dispute_id), 
	UNIQUE (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_disputes_user_id ON disputes (user_id);
CREATE INDEX ix_disputes_buyer_transaction_id ON disputes (buyer_transaction_id);
CREATE INDEX idx_dispute_state ON disputes (dispute_state);
CREATE INDEX idx_dispute_status ON disputes (status);
CREATE INDEX ix_disputes_seller_transaction_id ON disputes (seller_transaction_id);
CREATE INDEX idx_dispute_reason ON disputes (reason);
CREATE INDEX idx_dispute_create_time ON disputes (create_time);
CREATE INDEX ix_disputes_disputed_transaction_id ON disputes (disputed_transaction_id);
CREATE INDEX idx_dispute_user ON disputes (user_id);
CREATE TABLE invoices (
	id VARCHAR(30) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	detail JSON NOT NULL, 
	invoicer JSON, 
	primary_recipients JSON, 
	additional_recipients JSON, 
	amount JSON, 
	due_date DATE, 
	create_time DATETIME DEFAULT CURRENT_TIMESTAMP, 
	update_time DATETIME, 
	updated_at DATETIME, 
	parent_id VARCHAR(30), 
	gratuity JSON, 
	sent_at DATETIME, 
	scheduled_at DATETIME, 
	last_modified_by VARCHAR(100), 
	notification_settings JSON, 
	user_id VARCHAR(13) NOT NULL, 
	configuration JSON, 
	due_amount JSON, 
	links JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_invoice_user ON invoices (user_id);
CREATE INDEX idx_invoice_create_time ON invoices (create_time);
CREATE INDEX ix_invoices_user_id ON invoices (user_id);
CREATE INDEX idx_invoice_status ON invoices (status);
CREATE INDEX ix_invoices_parent_id ON invoices (parent_id);
CREATE INDEX idx_invoice_due_date ON invoices (due_date);
CREATE TABLE invoice_templates (
	id VARCHAR(30) NOT NULL, 
	name VARCHAR(500), 
	default_template BOOLEAN, 
	template_info JSON, 
	settings JSON, 
	unit_of_measure VARCHAR(8), 
	standard_template BOOLEAN, 
	user_id VARCHAR(13) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_invoice_templates_user_id ON invoice_templates (user_id);
CREATE INDEX idx_template_name ON invoice_templates (name);
CREATE INDEX idx_template_default ON invoice_templates (default_template);
CREATE INDEX idx_template_standard ON invoice_templates (standard_template);
CREATE INDEX ix_invoice_templates_name ON invoice_templates (name);
CREATE TABLE invoice_number_sequences (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	prefix VARCHAR(50) NOT NULL, 
	current_number INTEGER NOT NULL, 
	suffix_pattern VARCHAR(50), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	padding_zeros INTEGER NOT NULL, 
	reset_yearly BOOLEAN NOT NULL, 
	reset_monthly BOOLEAN NOT NULL, 
	last_reset_date DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_invoice_number_sequences_user_id ON invoice_number_sequences (user_id);
CREATE TABLE generated_invoice_numbers (
	id INTEGER NOT NULL, 
	invoice_number VARCHAR(25) NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	sequence_id INTEGER, 
	generated_at DATETIME NOT NULL, 
	generated_by VARCHAR(100), 
	request_type VARCHAR(20) NOT NULL, 
	is_used BOOLEAN NOT NULL, 
	used_at DATETIME, 
	invoice_id VARCHAR(30), 
	extra_metadata JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE UNIQUE INDEX ix_generated_invoice_numbers_invoice_number ON generated_invoice_numbers (invoice_number);
CREATE INDEX ix_generated_invoice_numbers_user_id ON generated_invoice_numbers (user_id);
CREATE TABLE payout_batches (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	sender_batch_id VARCHAR(256) NOT NULL, 
	payout_batch_id VARCHAR(50) NOT NULL, 
	recipient_type VARCHAR(20), 
	email_subject VARCHAR(255), 
	email_message VARCHAR(1000), 
	note VARCHAR(165), 
	batch_status VARCHAR(10) NOT NULL, 
	total_amount FLOAT, 
	total_fee FLOAT, 
	currency VARCHAR(3), 
	total_items INTEGER, 
	processed_items INTEGER, 
	errors_count INTEGER, 
	time_created DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	time_completed DATETIME, 
	time_closed DATETIME, 
	time_updated DATETIME, 
	funding_source VARCHAR(36), 
	displayable VARCHAR(10), 
	sender_info JSON, 
	batch_metadata JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (payout_batch_id)
);
CREATE INDEX ix_payout_batches_user_id ON payout_batches (user_id);
CREATE INDEX ix_payout_batches_sender_batch_id ON payout_batches (sender_batch_id);
CREATE TABLE referenced_payout_batches (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	batch_id VARCHAR(50) NOT NULL, 
	sender_batch_id VARCHAR(256), 
	batch_status VARCHAR(20) NOT NULL, 
	total_items FLOAT NOT NULL, 
	processed_items FLOAT NOT NULL, 
	success_items FLOAT NOT NULL, 
	failed_items FLOAT NOT NULL, 
	total_amount FLOAT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	total_fee FLOAT, 
	time_created DATETIME NOT NULL, 
	time_completed DATETIME, 
	batch_metadata JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (batch_id)
);
CREATE INDEX ix_referenced_payout_batches_user_id ON referenced_payout_batches (user_id);
CREATE UNIQUE INDEX ix_referenced_payout_batches_sender_batch_id ON referenced_payout_batches (sender_batch_id);
CREATE TABLE payment_authorizations (
	id VARCHAR(50) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	amount_currency_code VARCHAR(3) NOT NULL, 
	amount_value VARCHAR(20) NOT NULL, 
	invoice_id VARCHAR(30), 
	custom_id VARCHAR(255), 
	reason_code VARCHAR(50), 
	seller_protection_status VARCHAR(50), 
	seller_protection_dispute_categories JSON, 
	processor_avs_code VARCHAR(10), 
	processor_cvv_code VARCHAR(10), 
	processor_response_code VARCHAR(10), 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	expiration_time DATETIME, 
	order_id VARCHAR(50), 
	payer_email VARCHAR(254), 
	user_id VARCHAR(13), 
	raw_response JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_payment_authorizations_user_id ON payment_authorizations (user_id);
CREATE TABLE authorization_captures (
	id VARCHAR(50) NOT NULL, 
	authorization_id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	amount_currency_code VARCHAR(3) NOT NULL, 
	amount_value VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	final_capture BOOLEAN NOT NULL, 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	disbursement_mode VARCHAR(20), 
	invoice_id VARCHAR(30), 
	note_to_payer TEXT, 
	raw_response JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_authorization_captures_user_id ON authorization_captures (user_id);
CREATE INDEX ix_authorization_captures_authorization_id ON authorization_captures (authorization_id);
CREATE TABLE capture_refunds (
	id VARCHAR(50) NOT NULL, 
	capture_id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	amount_currency_code VARCHAR(3) NOT NULL, 
	amount_value VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	invoice_id VARCHAR(30), 
	note_to_payer VARCHAR(255), 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	raw_response JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_capture_refunds_capture_id ON capture_refunds (capture_id);
CREATE INDEX ix_capture_refunds_user_id ON capture_refunds (user_id);
CREATE TABLE reporting_balances (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	account_id VARCHAR(50) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	is_primary BOOLEAN, 
	total_balance NUMERIC(19, 2) NOT NULL, 
	available_balance NUMERIC(19, 2) NOT NULL, 
	withheld_balance NUMERIC(19, 2) NOT NULL, 
	pending_balance NUMERIC(19, 2) NOT NULL, 
	reserve_balance NUMERIC(19, 2) NOT NULL, 
	instant_balance NUMERIC(19, 2) NOT NULL, 
	as_of_time DATETIME NOT NULL, 
	last_refresh_time DATETIME NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	deleted BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_user_currency ON reporting_balances (user_id, currency);
CREATE INDEX idx_account_currency ON reporting_balances (account_id, currency);
CREATE INDEX ix_reporting_balances_currency ON reporting_balances (currency);
CREATE INDEX ix_reporting_balances_as_of_time ON reporting_balances (as_of_time);
CREATE INDEX ix_reporting_balances_user_id ON reporting_balances (user_id);
CREATE INDEX idx_user_time ON reporting_balances (user_id, as_of_time);
CREATE TABLE reporting_crypto_balances (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	account_id VARCHAR(50) NOT NULL, 
	asset_symbol VARCHAR(10) NOT NULL, 
	quantity VARCHAR(50) NOT NULL, 
	as_of_time DATETIME NOT NULL, 
	last_refresh_time DATETIME NOT NULL, 
	created_at DATETIME, 
	updated_at DATETIME, 
	deleted BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_crypto_user_symbol ON reporting_crypto_balances (user_id, asset_symbol);
CREATE INDEX ix_reporting_crypto_balances_user_id ON reporting_crypto_balances (user_id);
CREATE INDEX ix_reporting_crypto_balances_asset_symbol ON reporting_crypto_balances (asset_symbol);
CREATE INDEX ix_reporting_crypto_balances_as_of_time ON reporting_crypto_balances (as_of_time);
CREATE INDEX idx_crypto_user_time ON reporting_crypto_balances (user_id, as_of_time);
CREATE TABLE balance_snapshots (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	account_id VARCHAR(50) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	total_balance NUMERIC(19, 2) NOT NULL, 
	available_balance NUMERIC(19, 2) NOT NULL, 
	withheld_balance NUMERIC(19, 2) NOT NULL, 
	snapshot_time DATETIME NOT NULL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_balance_snapshots_snapshot_time ON balance_snapshots (snapshot_time);
CREATE INDEX idx_snapshot_user_currency_time ON balance_snapshots (user_id, currency, snapshot_time);
CREATE INDEX idx_snapshot_user_time ON balance_snapshots (user_id, snapshot_time);
CREATE INDEX ix_balance_snapshots_user_id ON balance_snapshots (user_id);
CREATE TABLE reporting_transactions (
	id VARCHAR(50) NOT NULL, 
	transaction_id VARCHAR(19) NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	paypal_account_id VARCHAR(50), 
	transaction_event_code VARCHAR(10), 
	transaction_type VARCHAR(50), 
	transaction_status VARCHAR(1), 
	transaction_subject VARCHAR(255), 
	transaction_note VARCHAR(255), 
	invoice_id VARCHAR(50), 
	custom_field VARCHAR(255), 
	protection_eligibility VARCHAR(50), 
	credit_term VARCHAR(50), 
	payment_method_type VARCHAR(50), 
	instrument_type VARCHAR(50), 
	instrument_sub_type VARCHAR(50), 
	bank_reference_id VARCHAR(100), 
	credit_transaction_reference VARCHAR(100), 
	transaction_initiation_date DATETIME NOT NULL, 
	transaction_updated_date DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	transaction_amount NUMERIC(19, 2), 
	transaction_currency VARCHAR(3), 
	fee_amount NUMERIC(19, 2), 
	fee_currency VARCHAR(3), 
	insurance_amount NUMERIC(19, 2), 
	shipping_amount NUMERIC(19, 2), 
	shipping_discount_amount NUMERIC(19, 2), 
	ending_balance NUMERIC(19, 2), 
	available_balance NUMERIC(19, 2), 
	balance_affecting BOOLEAN, 
	deleted BOOLEAN, 
	payer_info JSON, 
	shipping_info JSON, 
	cart_info JSON, 
	store_info JSON, 
	auction_info JSON, 
	incentive_info JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_reporting_transactions_transaction_id ON reporting_transactions (transaction_id);
CREATE INDEX ix_reporting_transactions_transaction_initiation_date ON reporting_transactions (transaction_initiation_date);
CREATE INDEX ix_reporting_transactions_user_id ON reporting_transactions (user_id);
CREATE INDEX idx_user_type ON reporting_transactions (user_id, transaction_type);
CREATE INDEX idx_user_status ON reporting_transactions (user_id, transaction_status);
CREATE INDEX idx_user_date ON reporting_transactions (user_id, transaction_initiation_date);
CREATE INDEX ix_reporting_transactions_invoice_id ON reporting_transactions (invoice_id);
CREATE TABLE shipping_trackers (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	order_id VARCHAR(36), 
	transaction_id VARCHAR(50) NOT NULL, 
	tracking_number VARCHAR(64), 
	tracking_number_type VARCHAR(50), 
	status VARCHAR(50) NOT NULL, 
	shipment_date DATETIME, 
	last_updated_time DATETIME, 
	carrier VARCHAR(64), 
	carrier_name_other VARCHAR(64), 
	postage_payment_id VARCHAR(64), 
	notify_buyer BOOLEAN, 
	quantity INTEGER, 
	tracking_number_validated BOOLEAN, 
	shipment_direction VARCHAR(50), 
	shipment_uploader VARCHAR(50), 
	account_id VARCHAR(13), 
	tracking_url VARCHAR(250), 
	created_at DATETIME, 
	updated_at DATETIME, 
	deleted BOOLEAN, 
	additional_info JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_shipping_trackers_user_id ON shipping_trackers (user_id);
CREATE INDEX idx_shipping_user_order ON shipping_trackers (user_id, order_id);
CREATE INDEX idx_shipping_transaction_tracking ON shipping_trackers (transaction_id, tracking_number);
CREATE INDEX idx_shipping_user_transaction ON shipping_trackers (user_id, transaction_id);
CREATE INDEX idx_shipping_user_tracking ON shipping_trackers (user_id, tracking_number);
CREATE UNIQUE INDEX idx_unique_shipping_user_order_track ON shipping_trackers (user_id, order_id, tracking_number);
CREATE INDEX ix_shipping_trackers_status ON shipping_trackers (status);
CREATE INDEX idx_shipping_user_status ON shipping_trackers (user_id, status);
CREATE INDEX ix_shipping_trackers_tracking_number ON shipping_trackers (tracking_number);
CREATE INDEX ix_shipping_trackers_transaction_id ON shipping_trackers (transaction_id);
CREATE INDEX idx_shipping_order_tracking ON shipping_trackers (order_id, tracking_number);
CREATE UNIQUE INDEX idx_unique_shipping_user_trans_track ON shipping_trackers (user_id, transaction_id, tracking_number);
CREATE INDEX ix_shipping_trackers_order_id ON shipping_trackers (order_id);
CREATE TABLE tracking_events (
	id INTEGER NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	tracker_id INTEGER NOT NULL, 
	transaction_id VARCHAR(50) NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	old_value VARCHAR(255), 
	new_value VARCHAR(255), 
	event_description VARCHAR(500), 
	event_time DATETIME, 
	triggered_by VARCHAR(255), 
	event_data JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_event_transaction ON tracking_events (transaction_id);
CREATE INDEX idx_event_user_tracker ON tracking_events (user_id, tracker_id);
CREATE INDEX ix_tracking_events_tracker_id ON tracking_events (tracker_id);
CREATE INDEX ix_tracking_events_user_id ON tracking_events (user_id);
CREATE INDEX ix_tracking_events_event_time ON tracking_events (event_time);
CREATE INDEX idx_event_user_time ON tracking_events (user_id, event_time);
CREATE INDEX ix_tracking_events_transaction_id ON tracking_events (transaction_id);
CREATE TABLE vault_payment_tokens (
	id VARCHAR(50) NOT NULL, 
	setup_token_id VARCHAR(50) NOT NULL, 
	customer_id VARCHAR(100), 
	merchant_customer_id VARCHAR(100), 
	payment_source_type VARCHAR(20) NOT NULL, 
	payment_source_data JSON NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	client_id VARCHAR(100), 
	created_at DATETIME NOT NULL, 
	metadata_json JSON, 
	is_active BOOLEAN NOT NULL, 
	is_primary BOOLEAN NOT NULL, 
	last_used_at DATETIME, 
	usage_count VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_vault_payment_tokens_setup_token_id ON vault_payment_tokens (setup_token_id);
CREATE INDEX ix_vault_payment_tokens_merchant_customer_id ON vault_payment_tokens (merchant_customer_id);
CREATE INDEX ix_vault_payment_tokens_client_id ON vault_payment_tokens (client_id);
CREATE INDEX ix_vault_payment_tokens_customer_id ON vault_payment_tokens (customer_id);
CREATE INDEX ix_vault_payment_tokens_user_id ON vault_payment_tokens (user_id);
CREATE INDEX ix_vault_payment_tokens_id ON vault_payment_tokens (id);
CREATE TABLE vault_setup_tokens (
	id VARCHAR(50) NOT NULL, 
	customer_id VARCHAR(100), 
	merchant_customer_id VARCHAR(100), 
	payment_source_type VARCHAR(20) NOT NULL, 
	payment_source_data JSON NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	approval_url TEXT, 
	approved_at DATETIME, 
	request_id VARCHAR(100), 
	user_id VARCHAR(13) NOT NULL, 
	client_id VARCHAR(100), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	expires_at DATETIME, 
	experience_context JSON, 
	additional_data JSON, 
	verification_status VARCHAR(50), 
	verification_method VARCHAR(50), 
	experience_status VARCHAR(30), 
	app_switch_eligibility BOOLEAN, 
	authentication JSON, 
	converted_to_payment_token BOOLEAN NOT NULL, 
	payment_token_id VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_vault_setup_tokens_id ON vault_setup_tokens (id);
CREATE INDEX ix_vault_setup_tokens_client_id ON vault_setup_tokens (client_id);
CREATE INDEX ix_vault_setup_tokens_customer_id ON vault_setup_tokens (customer_id);
CREATE UNIQUE INDEX ix_vault_setup_tokens_request_id ON vault_setup_tokens (request_id);
CREATE INDEX ix_vault_setup_tokens_payment_token_id ON vault_setup_tokens (payment_token_id);
CREATE INDEX ix_vault_setup_tokens_user_id ON vault_setup_tokens (user_id);
CREATE INDEX ix_vault_setup_tokens_merchant_customer_id ON vault_setup_tokens (merchant_customer_id);
CREATE TABLE payers (
	id VARCHAR(50) NOT NULL, 
	order_id VARCHAR(50) NOT NULL, 
	email_address VARCHAR(254), 
	user_id VARCHAR(13), 
	name_prefix VARCHAR(100), 
	given_name VARCHAR(150), 
	middle_name VARCHAR(150), 
	surname VARCHAR(150), 
	name_suffix VARCHAR(100), 
	full_name VARCHAR(300), 
	phone_type VARCHAR(6), 
	phone_country_code VARCHAR(5), 
	phone_national_number VARCHAR(20), 
	phone_extension VARCHAR(15), 
	address JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_payers_order_id ON payers (order_id);
CREATE INDEX ix_payers_user_id ON payers (user_id);
CREATE TABLE purchase_units (
	id VARCHAR(50) NOT NULL, 
	order_id VARCHAR(50) NOT NULL, 
	reference_id VARCHAR(256), 
	description VARCHAR(512), 
	custom_id VARCHAR(127), 
	invoice_id VARCHAR(127), 
	soft_descriptor VARCHAR(255), 
	currency_code VARCHAR(3) NOT NULL, 
	value VARCHAR(50) NOT NULL, 
	amount_breakdown JSON, 
	shipping_name JSON, 
	shipping_address JSON, 
	payee JSON, 
	supplementary_data JSON, 
	payment_instruction JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
);
CREATE INDEX idx_purchase_units_invoice_id ON purchase_units (invoice_id);
CREATE INDEX idx_purchase_units_reference_id ON purchase_units (reference_id);
CREATE INDEX ix_purchase_units_order_id ON purchase_units (order_id);
CREATE TABLE order_status_history (
	id VARCHAR(50) NOT NULL, 
	order_id VARCHAR(50) NOT NULL, 
	status VARCHAR(21) NOT NULL, 
	status_time DATETIME NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE
);
CREATE INDEX ix_order_status_history_order_id ON order_status_history (order_id);
CREATE TABLE billing_plans (
	id VARCHAR(50) NOT NULL, 
	product_id VARCHAR(50) NOT NULL, 
	name VARCHAR(127) NOT NULL, 
	description VARCHAR(127), 
	status VARCHAR(8) NOT NULL, 
	billing_cycles JSON NOT NULL, 
	payment_preferences JSON, 
	taxes JSON, 
	merchant_preferences JSON, 
	quantity_supported BOOLEAN NOT NULL, 
	create_time DATETIME NOT NULL, 
	update_time DATETIME NOT NULL, 
	user_id VARCHAR(13), 
	request_id VARCHAR(255), 
	request_id_created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_billing_plans_user_id ON billing_plans (user_id);
CREATE INDEX ix_billing_plans_product_id ON billing_plans (product_id);
CREATE INDEX ix_billing_plans_id ON billing_plans (id);
CREATE UNIQUE INDEX ix_billing_plans_request_id ON billing_plans (request_id);
CREATE TABLE webhook_event_subscriptions (
	webhook_id VARCHAR(50) NOT NULL, 
	event_type_id INTEGER NOT NULL, 
	PRIMARY KEY (webhook_id, event_type_id), 
	FOREIGN KEY(webhook_id) REFERENCES webhooks (id) ON DELETE CASCADE, 
	FOREIGN KEY(event_type_id) REFERENCES webhook_event_types (id)
);
CREATE TABLE webhook_signatures (
	id INTEGER NOT NULL, 
	auth_algo VARCHAR(100) NOT NULL, 
	cert_url VARCHAR(500) NOT NULL, 
	transmission_id VARCHAR(50) NOT NULL, 
	transmission_sig VARCHAR(500) NOT NULL, 
	transmission_time VARCHAR(100) NOT NULL, 
	webhook_id VARCHAR(50) NOT NULL, 
	webhook_event JSON NOT NULL, 
	verification_status VARCHAR(20) NOT NULL, 
	verified_at DATETIME, 
	user_id VARCHAR(13) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES webhooks (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX ix_webhook_signatures_id ON webhook_signatures (id);
CREATE INDEX ix_webhook_signatures_webhook_id ON webhook_signatures (webhook_id);
CREATE INDEX ix_webhook_signatures_user_id ON webhook_signatures (user_id);
CREATE INDEX ix_webhook_signatures_auth_algo ON webhook_signatures (auth_algo);
CREATE UNIQUE INDEX ix_webhook_signatures_transmission_id ON webhook_signatures (transmission_id);
CREATE TABLE webhook_lookup_event_types (
	id VARCHAR(36) NOT NULL, 
	webhook_id VARCHAR(17) NOT NULL, 
	event_name VARCHAR(255) NOT NULL, 
	description TEXT, 
	status VARCHAR(50) NOT NULL, 
	resource_versions JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES webhook_lookups (id) ON DELETE CASCADE
);
CREATE INDEX idx_webhook_event_name ON webhook_lookup_event_types (webhook_id, event_name);
CREATE INDEX idx_webhook_event_webhook_id ON webhook_lookup_event_types (webhook_id);
CREATE TABLE referral_events (
	id VARCHAR(50) NOT NULL, 
	referral_id VARCHAR(50) NOT NULL, 
	event_type VARCHAR(50) NOT NULL, 
	event_data JSON, 
	event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	actor_type VARCHAR(50), 
	actor_id VARCHAR(100), 
	PRIMARY KEY (id), 
	FOREIGN KEY(referral_id) REFERENCES partner_referrals (id)
);
CREATE INDEX ix_referral_events_id ON referral_events (id);
CREATE TABLE oauth_applications (
	id VARCHAR(50) NOT NULL, 
	client_id VARCHAR(80) NOT NULL, 
	client_secret VARCHAR(255) NOT NULL, 
	environment VARCHAR(10) NOT NULL, 
	application_name VARCHAR(255), 
	webhook_id VARCHAR(50), 
	status VARCHAR(9) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	user_id VARCHAR(13), 
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES webhooks (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE UNIQUE INDEX ix_oauth_applications_client_id ON oauth_applications (client_id);
CREATE INDEX ix_oauth_applications_status ON oauth_applications (status);
CREATE INDEX ix_oauth_applications_environment ON oauth_applications (environment);
CREATE INDEX ix_oauth_applications_user_id ON oauth_applications (user_id);
CREATE INDEX ix_oauth_applications_id ON oauth_applications (id);
CREATE TABLE dispute_messages (
	id VARCHAR(50) NOT NULL, 
	dispute_id VARCHAR(50) NOT NULL, 
	posted_by VARCHAR(6) NOT NULL, 
	time_posted DATETIME DEFAULT CURRENT_TIMESTAMP, 
	content TEXT(2000) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(dispute_id) REFERENCES disputes (dispute_id)
);
CREATE INDEX idx_dispute_message_time ON dispute_messages (time_posted);
CREATE INDEX ix_dispute_messages_dispute_id ON dispute_messages (dispute_id);
CREATE INDEX idx_dispute_message_posted_by ON dispute_messages (posted_by);
CREATE TABLE dispute_evidence (
	id VARCHAR(50) NOT NULL, 
	dispute_id VARCHAR(50) NOT NULL, 
	evidence_type VARCHAR(22) NOT NULL, 
	evidence_info JSON, 
	time_posted DATETIME DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(dispute_id) REFERENCES disputes (dispute_id)
);
CREATE INDEX ix_dispute_evidence_dispute_id ON dispute_evidence (dispute_id);
CREATE INDEX idx_dispute_evidence_time ON dispute_evidence (time_posted);
CREATE INDEX idx_dispute_evidence_type ON dispute_evidence (evidence_type);
CREATE TABLE invoice_items (
	id VARCHAR(22) NOT NULL, 
	invoice_id VARCHAR(30) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description VARCHAR(1000), 
	quantity VARCHAR(10) NOT NULL, 
	unit_amount_value NUMERIC(19, 6) NOT NULL, 
	unit_amount_currency VARCHAR(3) NOT NULL, 
	tax JSON, 
	tax_name VARCHAR(100), 
	tax_percent NUMERIC(5, 2), 
	position INTEGER, 
	item_date DATE, 
	discount JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id)
);
CREATE INDEX ix_invoice_items_invoice_id ON invoice_items (invoice_id);
CREATE INDEX idx_invoice_item_name ON invoice_items (name);
CREATE TABLE invoice_payments (
	id VARCHAR(22) NOT NULL, 
	invoice_id VARCHAR(30) NOT NULL, 
	payment_type VARCHAR(20) NOT NULL, 
	payment_method VARCHAR(50) NOT NULL, 
	payment_date DATE NOT NULL, 
	amount_value NUMERIC(19, 6) NOT NULL, 
	amount_currency VARCHAR(3) NOT NULL, 
	transaction_id VARCHAR(100), 
	note TEXT, 
	shipping_info JSON, 
	created_at DATETIME NOT NULL, 
	created_by VARCHAR(100) NOT NULL, 
	user_id VARCHAR(13) NOT NULL, 
	is_partial BOOLEAN, 
	remaining_balance VARCHAR(20), 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_payment_date ON invoice_payments (payment_date);
CREATE INDEX idx_payment_user ON invoice_payments (user_id);
CREATE INDEX idx_payment_transaction ON invoice_payments (transaction_id);
CREATE INDEX ix_invoice_payments_invoice_id ON invoice_payments (invoice_id);
CREATE INDEX ix_invoice_payments_user_id ON invoice_payments (user_id);
CREATE INDEX idx_payment_invoice ON invoice_payments (invoice_id);
CREATE TABLE invoice_activities (
	id VARCHAR(30) NOT NULL, 
	invoice_id VARCHAR(30) NOT NULL, 
	activity_type VARCHAR(50) NOT NULL, 
	activity_date DATETIME NOT NULL, 
	performed_by VARCHAR(100) NOT NULL, 
	old_status VARCHAR(50), 
	new_status VARCHAR(50), 
	details JSON, 
	user_id VARCHAR(13) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE INDEX idx_activity_type ON invoice_activities (activity_type);
CREATE INDEX ix_invoice_activities_activity_date ON invoice_activities (activity_date);
CREATE INDEX idx_activity_date ON invoice_activities (activity_date);
CREATE INDEX idx_activity_user ON invoice_activities (user_id);
CREATE INDEX idx_activity_invoice_type ON invoice_activities (invoice_id, activity_type);
CREATE INDEX ix_invoice_activities_invoice_id ON invoice_activities (invoice_id);
CREATE INDEX ix_invoice_activities_activity_type ON invoice_activities (activity_type);
CREATE INDEX ix_invoice_activities_user_id ON invoice_activities (user_id);
CREATE INDEX idx_activity_invoice ON invoice_activities (invoice_id);
CREATE TABLE payout_items (
	id VARCHAR(50) NOT NULL, 
	payout_batch_id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	payout_item_id VARCHAR(50) NOT NULL, 
	sender_item_id VARCHAR(256), 
	transaction_id VARCHAR(50), 
	activity_id VARCHAR(50), 
	recipient_type VARCHAR(20), 
	receiver VARCHAR(127) NOT NULL, 
	recipient_wallet VARCHAR(20), 
	recipient_name VARCHAR(255), 
	amount FLOAT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	fee_amount FLOAT, 
	fee_currency VARCHAR(3), 
	transaction_status VARCHAR(9) NOT NULL, 
	note VARCHAR(165), 
	notification_language VARCHAR(10), 
	purpose VARCHAR(40), 
	alternate_notification JSON, 
	application_context JSON, 
	currency_conversion JSON, 
	errors JSON, 
	time_processed DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(payout_batch_id) REFERENCES payout_batches (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (payout_item_id)
);
CREATE INDEX ix_payout_items_transaction_id ON payout_items (transaction_id);
CREATE INDEX ix_payout_items_receiver ON payout_items (receiver);
CREATE INDEX ix_payout_items_sender_item_id ON payout_items (sender_item_id);
CREATE INDEX ix_payout_items_user_id ON payout_items (user_id);
CREATE INDEX ix_payout_items_payout_batch_id ON payout_items (payout_batch_id);
CREATE TABLE referenced_payout_items (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	item_id VARCHAR(256) NOT NULL, 
	processing_state_status VARCHAR(50) NOT NULL, 
	processing_state_reason VARCHAR(100) NOT NULL, 
	reference_id VARCHAR(256) NOT NULL, 
	reference_type VARCHAR(14) NOT NULL, 
	payout_transaction_id VARCHAR(256) NOT NULL, 
	disbursement_transaction_id VARCHAR(256) NOT NULL, 
	external_merchant_id VARCHAR(256) NOT NULL, 
	external_reference_id VARCHAR(256) NOT NULL, 
	payout_destination VARCHAR(256) NOT NULL, 
	invoice_id VARCHAR(256) NOT NULL, 
	custom VARCHAR(256) NOT NULL, 
	payee_email VARCHAR(254) NOT NULL, 
	payout_amount_value VARCHAR(50) NOT NULL, 
	payout_amount_currency VARCHAR(3) NOT NULL, 
	links JSON NOT NULL, 
	time_created DATETIME NOT NULL, 
	time_updated DATETIME, 
	payout_batch_id VARCHAR(50), 
	item_metadata JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(payout_batch_id) REFERENCES referenced_payout_batches (batch_id)
);
CREATE INDEX ix_referenced_payout_items_reference_id ON referenced_payout_items (reference_id);
CREATE UNIQUE INDEX ix_referenced_payout_items_item_id ON referenced_payout_items (item_id);
CREATE INDEX ix_referenced_payout_items_payout_batch_id ON referenced_payout_items (payout_batch_id);
CREATE INDEX idx_ref_payout_user_reference ON referenced_payout_items (user_id, reference_id);
CREATE INDEX idx_ref_payout_payee_email ON referenced_payout_items (payee_email);
CREATE INDEX idx_ref_payout_external_merchant ON referenced_payout_items (external_merchant_id);
CREATE INDEX idx_ref_payout_user_item ON referenced_payout_items (user_id, item_id);
CREATE INDEX ix_referenced_payout_items_user_id ON referenced_payout_items (user_id);
CREATE INDEX idx_ref_payout_user_created ON referenced_payout_items (user_id, time_created);
CREATE INDEX ix_referenced_payout_items_payee_email ON referenced_payout_items (payee_email);
CREATE TABLE purchase_unit_items (
	id VARCHAR(50) NOT NULL, 
	purchase_unit_id VARCHAR(50) NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	description VARCHAR(512), 
	sku VARCHAR(127), 
	unit_amount JSON NOT NULL, 
	tax JSON, 
	quantity VARCHAR(20) NOT NULL, 
	category VARCHAR(14), 
	PRIMARY KEY (id), 
	FOREIGN KEY(purchase_unit_id) REFERENCES purchase_units (id) ON DELETE CASCADE
);
CREATE INDEX ix_purchase_unit_items_purchase_unit_id ON purchase_unit_items (purchase_unit_id);
CREATE TABLE subscriptions (
	id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(13), 
	plan_id VARCHAR(50) NOT NULL, 
	start_time DATETIME, 
	status VARCHAR(16) NOT NULL, 
	status_change_note VARCHAR(128), 
	status_update_time DATETIME, 
	quantity VARCHAR(32), 
	shipping_amount_value NUMERIC(19, 6), 
	shipping_amount_currency VARCHAR(3), 
	subscriber_id VARCHAR(50), 
	custom_id VARCHAR(127), 
	plan_overridden BOOLEAN NOT NULL, 
	create_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	update_time DATETIME, 
	application_context JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(plan_id) REFERENCES billing_plans (id), 
	FOREIGN KEY(subscriber_id) REFERENCES subscribers (id)
);
CREATE INDEX idx_subscription_create_time ON subscriptions (create_time);
CREATE INDEX ix_subscriptions_user_id ON subscriptions (user_id);
CREATE INDEX ix_subscriptions_plan_id ON subscriptions (plan_id);
CREATE INDEX idx_subscription_status ON subscriptions (status);
CREATE INDEX ix_subscriptions_subscriber_id ON subscriptions (subscriber_id);
CREATE TABLE oauth_access_tokens (
	id VARCHAR(50) NOT NULL, 
	application_id VARCHAR(50) NOT NULL, 
	user_id VARCHAR(255), 
	access_token VARCHAR(2048) NOT NULL, 
	token_type VARCHAR(6) NOT NULL, 
	scope VARCHAR(4096), 
	expires_in INTEGER, 
	expires_at DATETIME NOT NULL, 
	app_id VARCHAR(50), 
	nonce VARCHAR(255), 
	status VARCHAR(7) NOT NULL, 
	created_at DATETIME NOT NULL, 
	last_used_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES oauth_applications (id) ON DELETE cascade, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE cascade
);
CREATE INDEX ix_oauth_access_tokens_id ON oauth_access_tokens (id);
CREATE INDEX ix_oauth_access_tokens_user_id ON oauth_access_tokens (user_id);
CREATE INDEX ix_oauth_access_tokens_app_id ON oauth_access_tokens (app_id);
CREATE INDEX ix_oauth_access_tokens_status ON oauth_access_tokens (status);
CREATE INDEX ix_oauth_access_tokens_application_id ON oauth_access_tokens (application_id);
CREATE INDEX ix_oauth_access_tokens_expires_at ON oauth_access_tokens (expires_at);
CREATE TABLE subscription_billing_info (
	subscription_id VARCHAR(50) NOT NULL, 
	outstanding_balance_value NUMERIC(19, 6) NOT NULL, 
	outstanding_balance_currency VARCHAR(3) NOT NULL, 
	next_billing_time DATETIME, 
	final_payment_time DATETIME, 
	failed_payments_count INTEGER NOT NULL, 
	last_payment_amount_value NUMERIC(19, 6), 
	last_payment_amount_currency VARCHAR(3), 
	last_payment_time DATETIME, 
	PRIMARY KEY (subscription_id), 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
);
CREATE INDEX idx_billing_info_failed_count ON subscription_billing_info (failed_payments_count);
CREATE INDEX idx_billing_info_next_billing ON subscription_billing_info (next_billing_time);
CREATE TABLE cycle_executions (
	id VARCHAR(50) NOT NULL, 
	subscription_id VARCHAR(50) NOT NULL, 
	tenure_type VARCHAR(7) NOT NULL, 
	sequence INTEGER NOT NULL, 
	cycles_completed INTEGER NOT NULL, 
	cycles_remaining INTEGER, 
	current_pricing_scheme_version INTEGER NOT NULL, 
	total_cycles INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
);
CREATE INDEX idx_cycle_execution_tenure ON cycle_executions (tenure_type);
CREATE INDEX idx_cycle_execution_sequence ON cycle_executions (sequence);
CREATE INDEX ix_cycle_executions_subscription_id ON cycle_executions (subscription_id);
CREATE TABLE subscription_transactions (
	id VARCHAR(50) NOT NULL, 
	subscription_id VARCHAR(50) NOT NULL, 
	status VARCHAR(18) NOT NULL, 
	gross_amount_value NUMERIC(19, 6) NOT NULL, 
	gross_amount_currency VARCHAR(3) NOT NULL, 
	fee_amount_value NUMERIC(19, 6), 
	fee_amount_currency VARCHAR(3), 
	net_amount_value NUMERIC(19, 6), 
	net_amount_currency VARCHAR(3), 
	payer_name VARCHAR(300), 
	payer_email VARCHAR(254), 
	time DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
);
CREATE INDEX ix_subscription_transactions_subscription_id ON subscription_transactions (subscription_id);
CREATE INDEX idx_subscription_transaction_status ON subscription_transactions (status);
CREATE INDEX idx_subscription_transaction_time ON subscription_transactions (time);
CREATE TABLE subscription_status_history (
	id VARCHAR(50) NOT NULL, 
	subscription_id VARCHAR(50) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	status_date DATETIME NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE CASCADE
);
CREATE INDEX ix_subscription_status_history_subscription_id ON subscription_status_history (subscription_id);
CREATE INDEX idx_status_history_created ON subscription_status_history (created_at);
CREATE INDEX idx_status_history_status ON subscription_status_history (status);
CREATE INDEX idx_status_history_date ON subscription_status_history (status_date);
