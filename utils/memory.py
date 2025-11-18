class MemoryManager:
	"""Minimal placeholder for shared agent memory."""

	def __init__(self):
		self._store = {}

	def get(self, key, default=None):
		return self._store.get(key, default)

	def set(self, key, value):
		self._store[key] = value
