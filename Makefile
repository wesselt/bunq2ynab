build-Bunq2YnabFunction:
	cp lambda_function.py $(ARTIFACTS_DIR)
	mkdir $(ARTIFACTS_DIR)/lib
	cp lib/*.py $(ARTIFACTS_DIR)/lib
