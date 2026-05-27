from mastodon import Mastodon

class MastodonClient:
    def __init__(self, instance_url: str, access_token: str):
        self.mastodon = Mastodon(
            access_token=access_token,
            api_base_url=instance_url
        )
        self._me = None

    def _get_my_id(self):
        if not self._me:
            self._me = self.mastodon.account_verify_credentials()
        return self._me['id']

    def fetch_toots(self, since_id=None, max_id=None, limit=40):
        """
        指定した since_id 以降、かつ max_id 以前の自アカウントのtootを取得する。
        APIは通常降順（最新のものが最初）で結果を返すため、
        必要に応じて呼出元でソートしてください。
        """
        my_id = self._get_my_id()
        params = {
            'id': my_id,
            'limit': limit
        }
        if since_id:
            params['since_id'] = since_id
        if max_id:
            params['max_id'] = max_id

        toots = self.mastodon.account_statuses(**params)
        return toots
