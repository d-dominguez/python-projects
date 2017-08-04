# Analyze the Kaggle Credit Card Fraud Data Set
# https://www.kaggle.com/dalpozz/creditcardfraud

import pandas as pd
import matplotlib.pyplot as plt


# Import credit card fraud dataset
fraud_df = pd.read_csv('creditcard.csv')

plt.plot(fraud_df)
plt.show()