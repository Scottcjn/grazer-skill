```python
class Moltbook:
    def __init__(self, options):
        self.options = options
        self.bounties_only = self.options.get('bounties-only', False)
    
    def get_discover_query(self):
        filter_keywords = ['bounty', 'reward', 'paid', 'hiring', 'commission', 'opportunity']
        query = f"""
            Table: Moltbook.Posts
            Columns: Id,Title,Content,Tags,Url,Score,Date, Created Time
            Filter:
                if contains any of {filter_keywords} in Tags or Content
                and if not contains any of ['task', 'job'] in Content
            Sort by:
                Created Time descending
            """
        return query

class Grazer:
    def discover(self, platform, options):
        if platform == 'moltbook':
            moltbook = Moltbook(options)
            return moltbook.get_discover_query()
        else:
            return "Platform not supported"

# Example usage:
print(Grazer().discover('moltbook', {'bounties-only': True}))
```