


#promene koje su >2% ce se pisati u bazu ostale promene se pisu u reddis


# def handle_battery_update(device_id, new_percentage):
#     cache_key = f"battery:{device_id}"
#     cached = redis.get(cache_key)

#     if cached:
#         old_percentage = float(cached["value"])
#         if abs(old_percentage - new_percentage) >= 2:
#             update_mysql(device_id, new_percentage)
#     else:
#         update_mysql(device_id, new_percentage)

#     # Always update cache
#     redis.set(cache_key, {"value": new_percentage, "timestamp": now()})