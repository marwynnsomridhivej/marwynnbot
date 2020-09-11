from fuzzywuzzy import process
from random import random


class FuzzySearch:
    def __init__(self, query: str, pool, limit: int = 10, threshold: int = 50):
        """Fuzzily searches for a query string in a given set of items

        Args:
            query (str): query to search for
            pool (Union[list, tuple]): pool to search from
            limit (int, optional): maximum number of results to return. Defaults to 10.
            threshold (int, optional): threshold for search confidence. Defaults to 50.
        """
        self.query = query
        self.pool = pool
        self.limit = limit
        self.threshold = threshold

    @classmethod
    def fuzzysearch(cls, query: str, pool, limit: int = 10, threshold: int = 50):
        """Constructor method that returns an instance of FuzzySearch

        Args:
            query (str): query to search for
            pool (Union[list, tuple]): pool to search from
            limit (int, optional): maximum number of results to return. Defaults to 10.
            threshold (int, optional): threshold for search confidence. Defaults to 50.

        Returns:
            class FuzzySearch: Fuzzily searches for a query string in a given set of items
        """
        return cls(query, pool, limit=limit, threshold=threshold)

    async def over_threshold(self):
        return [(name, confidence) for name, confidence in process.extract(self.query, self.pool, limit=self.limit) if confidence >= threshold]

    async def under_threshold(self):
        return [(name, confidence) for name, confidence in process.extract(self.query, self.pool, limit=self.limit) if confidence <= threshold]

    async def exact_threshold(self):
        return [(name, confidence) for name, confidence in process.extract(self.query, self.pool, limit=self.limit) if confidence == threshold]

    async def not_threshold(self):
        return [(name, confidence) for name, confidence in process.extract(self.query, self.pool, limit=self.limit) if confidence != threshold]

    async def random_over_threshold(self):
        return random.choice(await self.over_threshold())

    async def random_under_threshold(self):
        return random.chocie(await self.under_threshold())

    async def random_exact_threshold(self):
        return random.choice(await self.exact_threshold())

    async def random_not_threshold(self):
        return random.choice(await self.not_threshold)

class TagFuzzy(FuzzySearch):
    def __init__(self, query: str, pool, limit=10, threshold=70):
        """Fuzzily searches for a tag query in the guild's list of tags

        Args:
            query (str): tag name to search for
            pool (Union[list, tuple]): pool to search from
            limit (int, optional): maximum number of tag names to return. Defaults to 10.
            threshold (int, optional): threshold for search confidence. Defaults to 70.
        """
        super().__init__(query, pool, limit=limit, threshold=threshold)

    @classmethod
    def fuzzysearch(cls, query: str, pool, limit: int = 10, threshold: int = 70):
        """Constructor method that returns an instance of FuzzySearch

        Args:
            query (str): query to search for
            pool (Union[list, tuple]): pool to search from
            limit (int, optional): maximum number of results to return. Defaults to 10.
            threshold (int, optional): threshold for search confidence. Defaults to 70.

        Returns:
            class FuzzySearch: Fuzzily searches for a query string in a given set of items
        """
        return cls(query, pool, limit=limit, threshold=threshold)