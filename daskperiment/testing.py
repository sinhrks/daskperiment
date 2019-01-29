import os

IS_TRAVIS = "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true"
