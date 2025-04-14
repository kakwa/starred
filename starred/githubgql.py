from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

QUERY = gql("""
    query ($username: String!, $after: String) {
      user(login: $username) {
        lists(first: 100, after: $after) {
          nodes {
            id
            description
            name
            items(first: 100) {
              nodes {
                __typename
                ... on Repository {
                  name
                  nameWithOwner
                  description
                  url
                  stargazerCount
                  forkCount
                  isPrivate
                  pushedAt
                  updatedAt
                  owner {
                    login
                  }
                }
              }
            }
          }
          pageInfo {
            endCursor
            hasNextPage
          }
        }
      }
    }
    """
            )


class Repository:
    def __init__(self, name, description, url, stargazer_count, is_private, owner):
        self.name = name
        self.description = description
        self.url = url
        self.stargazer_count = stargazer_count
        self.is_private = is_private
        self.owner = owner


class List:
    def __init__(self, id, name, description, items):
        self.id = id
        self.name = name
        self.description = description
        self.items = items


class GitHubGQL:
    API_URL = "https://api.github.com/graphql"

    def __init__(self, token):
        self.token = token
        headers = {"Authorization": f"Bearer {token}"}
        self.transport = AIOHTTPTransport(url=self.API_URL, headers=headers)
        self.client = Client(transport=self.transport,
                             fetch_schema_from_transport=True)

    def get_user_starred_by_username(self, username: str, after: str = '', topic_stargazer_count_limit: int = 0):
        items = []
        result = self.client.execute(QUERY, variable_values={
                                     "username": username, "after": after})

        has_next = result['user']['lists']['pageInfo']['hasNextPage']
        end_cursor = result['user']['lists']['pageInfo']['endCursor']

        for list_node in result['user']['lists']['nodes']:
            list_items = []
            for item in list_node['items']['nodes']:
                if item['__typename'] == 'Repository':
                    repo = Repository(
                        name=item['nameWithOwner'],
                        description=item['description'] if item['description'] else '',
                        url=item['url'],
                        stargazer_count=item['stargazerCount'],
                        is_private=item['isPrivate'],
                        owner=item['owner']['login']
                    )
                    list_items.append(repo)

            list_obj = List(
                id=list_node['id'],
                name=list_node['name'],
                description=list_node['description'],
                items=list_items
            )
            items.append(list_obj)

        if has_next:
            items.extend(self.get_user_starred_by_username(
                username, end_cursor, topic_stargazer_count_limit))
        return items
