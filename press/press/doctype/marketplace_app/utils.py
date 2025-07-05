# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors

import frappe


def number_k_format(number: int):
	"""Returns a '101.6k' like string representation"""
	if number < 1000:
		return str(number)
	value = frappe.utils.rounded(number / 1000, precision=1)

	# To handle cases like 8.0, 9.0 etc.
	if value == (number // 1000) or (value - 1) == (number // 1000):
		value = int(value)

	return f"{value}k"


def get_rating_percentage_distribution(reviews: list) -> dict:
	"""
	Takes a list of app reviews and returns percentage distribution for ratings 1-5
	"""
	total_num_reviews = len(reviews)
	rating_frequencies = dict((i, 0) for i in range(1, 6))

	for review in reviews:
		rating_frequencies[review.rating] += 1

	if total_num_reviews > 0:
		rating_percentages = dict((k, (v * 100 // total_num_reviews)) for k, v in rating_frequencies.items())
		return rating_percentages
	# To handle the case when no reviews are present
	# All ratings are 0%
	return rating_frequencies
