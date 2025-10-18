"""
LinkedIn Enricher Agent
- Enriches candidate profiles using LinkedIn data via official APIs or scrapers
- Avoids scraping when ToS-disallowed; supports proxy provider abstractions
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from config import ENRICHMENT_CONFIG

@dataclass
class CandidateQuery:
    name: str
    email: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None

@dataclass
class LinkedInProfile:
    full_name: Optional[str]
    headline: Optional[str]
    url: Optional[str]
    location: Optional[str]
    current_company: Optional[str]
    current_title: Optional[str]
    experiences: list
    educations: list
    skills: list
    connections: Optional[int]

class LinkedInEnricher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.provider = self._init_provider()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('linkedin_enricher.log')]
        )
        return logging.getLogger(__name__)

    def _init_provider(self):
        # Support multiple providers: official API, proxy API, or search+people API
        provider = self.config.get('provider', 'proxy')
        client = {'name': provider}
        if provider == 'official':
            # Placeholder for LinkedIn Partner API client
            client['token'] = self.config.get('official', {}).get('access_token')
        elif provider == 'proxy':
            client['endpoint'] = self.config.get('proxy', {}).get('endpoint')
            client['api_key'] = self.config.get('proxy', {}).get('api_key')
        elif provider == 'serp':
            client['serp_key'] = self.config.get('serpapi', {}).get('api_key')
        return client

    def _proxy_lookup(self, query: CandidateQuery) -> Optional[Dict[str, Any]]:
        try:
            import requests
            endpoint = self.provider.get('endpoint')
            api_key = self.provider.get('api_key')
            if not endpoint or not api_key:
                return None
            payload = {
                'q': {
                    'name': query.name,
                    'email': query.email,
                    'company': query.company,
                    'title': query.title,
                    'location': query.location,
                },
                'fields': ['name','headline','url','location','experience','education','skills','connections','current_company','current_title']
            }
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            r = requests.post(endpoint, json=payload, headers=headers, timeout=45)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            self.logger.warning(f"Proxy lookup failed: {e}")
            return None

    def _serp_lookup(self, query: CandidateQuery) -> Optional[Dict[str, Any]]:
        try:
            import requests
            key = self.provider.get('serp_key')
            if not key:
                return None
            q = f"site:linkedin.com/in {query.name} {query.company or ''} {query.title or ''} {query.location or ''}"
            url = f"https://serpapi.com/search.json?q={requests.utils.quote(q)}&engine=google&api_key={key}"
            r = requests.get(url, timeout=45)
            r.raise_for_status()
            data = r.json()
            results = data.get('organic_results', [])
            if not results:
                return None
            # Return first candidate URL
            return {'url': results[0].get('link'), 'headline': results[0].get('title')}
        except Exception as e:
            self.logger.warning(f"Serp lookup failed: {e}")
            return None

    def enrich(self, query: CandidateQuery) -> LinkedInProfile:
        data = None
        if self.provider['name'] == 'proxy':
            data = self._proxy_lookup(query)
        elif self.provider['name'] == 'official':
            # Not implemented: requires partner access
            data = None
        elif self.provider['name'] == 'serp':
            data = self._serp_lookup(query)

        # Normalize
        profile = LinkedInProfile(
            full_name=(data or {}).get('name') or query.name,
            headline=(data or {}).get('headline'),
            url=(data or {}).get('url'),
            location=(data or {}).get('location'),
            current_company=(data or {}).get('current_company'),
            current_title=(data or {}).get('current_title'),
            experiences=(data or {}).get('experience') or [],
            educations=(data or {}).get('education') or [],
            skills=(data or {}).get('skills') or [],
            connections=(data or {}).get('connections'),
        )
        return profile

    def to_json(self, profile: LinkedInProfile) -> str:
        return json.dumps(asdict(profile), indent=2)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--email')
    parser.add_argument('--company')
    parser.add_argument('--title')
    parser.add_argument('--location')
    args = parser.parse_args()

    enricher = LinkedInEnricher(ENRICHMENT_CONFIG)
    profile = enricher.enrich(CandidateQuery(
        name=args.name,
        email=args.email,
        company=args.company,
        title=args.title,
        location=args.location,
    ))
    print(enricher.to_json(profile))

if __name__ == '__main__':
    main()
