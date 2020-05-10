###
# Copyright (c) 2020, Valentin Lorentz
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import json
import contextlib
from multiprocessing import Manager

from supybot import conf, utils
from supybot.test import *


PRIVATE_KEY = b"""
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA6jtjTlaTh1aR+q3gpZvb4dj8s81zKmwy7cwn44LtLV+ivNf/
SkWPr1zkm/gWFItC3058Faqk9p4fdJaxVJJTW0KL7LlJs+LTcMsLi2nTgvBZg7oE
KRXZxuJJcc5QNkgY8vHt1PxdD17mZBGwfg2loZfnjZOOz4F8wdQ18Da1ZFUFyc+R
qj1THdXbpBjF7zcNyJOWzzRwhpiqdJomnTAYDscAkkF2/gI8tYP+Is31GOE1phPC
DH20uvJNUtDnXSdUm2Ol21LmePV4pWS75mcIHz5YAKwAGo9XoUQa8lC6IHw6LX+y
CVKkoSc0Ouzr3acQCLZ8EDUIh2nMhw/VtYV7JwIDAQABAoIBAFSARkwtqZ1qmtFf
xyqXttScblYDaWfFjv4A5+cJBb2XweL03ZGS1MpD7elir7yLnP1omBVM8aRS2TA7
aRAElfPXZxloovE1hGgtqCWMcRTM1s5R3kxgKKe6XRqkfoWGrxF+O/nZbU0tRFqX
kx92lulcHtoRgLTVlwdqImddpUTjQrWmrt3nEjTZj5tHcPGdC2ovH/bFrganbCR1
If6xG2r6RWSfMEpj7yFTKRvnLCr2VpviDOwFh/zZdwyqBRKW6LNZP04TtlFfKh5C
1R2tZVRHQ7Ed99yruirW0rmgOjA6dJTpN6oX6x3DpTi48oK2jktEIk07P7jy1mZY
NeCQcqkCgYEA+M0DQ+0fBm/RJyDIxsupMAf8De1kG6Bj8gVSRnvtD0Fb3LTswT3I
TDnIVttjOzBsbpZVdjdCE9Wcfj9pIwu3YTO54OTS8kiwYRshzEm3UpdPOSCnIZUx
jwbbwEHq0zEeIWVjDBDXN2fqEcu7gFqBzYivAh8hYq78BJkUeBWU3N0CgYEA8QJ0
6xS551VEGLbn9h5pPxze7l8a9WJc1uIxRexeBtd4UwJ5e1yLN68FVNjGr3JtreJ3
KP/VyynFubNRvwGEnifKe9QyiATFCbVeAFBQFuA0w89LOmBiHc+uHz1uA5oXnD99
Y0pEu8g+QsBKeQowMhkYnw4h5cq3AVCKRIdNpdMCgYEAwy5p8l7SKQWNagnBGJtr
BeAtr2tdToL8BUCBdAQCTCZ0/2b8GPjz6kCmVuVTKnrphbPwJYZiExdP5oauXyzw
1pNyreg1SJcXr4ZOdGocI/HJ18Iy+xiEwXSa7m+H3dg5j+9uzWdkvvWJXh6a4K2g
CPLCgIKVeUpXMPA6a55aow0CgYAMpoRckonvipo4ceFbGd2MYoeRG4zetHsLDHRp
py6ITWcTdF3MC9+C3Lz65yYGr4ryRaDblhIyx86JINB5piq/4nbOaST93sI48Dwu
6AhMKxiZ7peUSNrdlbkeCqtrpPr4SJzcSVmyQaCDAHToRZCiEI8qSiOdXDae6wtW
7YM14QKBgQDnbseQK0yzrsZoOmQ9PBULr4vNLiL5+OllOG1+GNNztk/Q+Xfx6Hvw
h6cgTcpZsvaa2CW6A2yqenmGfKBgiRoN39vFqjVDkjL1HaL3rPeK1H7RWrz1Sto7
rut+UhYHat9fo6950Wvxa4Iee9q0NOF0HUkD6WupcPyC0nSEex8Z6A==
-----END RSA PRIVATE KEY-----
"""

HOSTMETA_URL = "https://example.org/.well-known/host-meta"
HOSTMETA_DATA = b"""<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Link rel="lrdd" type="application/xrd+xml" template="https://example.org/.well-known/webfinger?resource={uri}"/>
</XRD>
"""

WEBFINGER_URL = "https://example.org/.well-known/webfinger?resource=acct:someuser@example.org"
WEBFINGER_VALUE = {
    "subject": "acct:someuser@example.org",
    "aliases": [
        "https://example.org/@someuser",
        "https://example.org/users/someuser",
    ],
    "links": [
        {
            "rel": "http://webfinger.net/rel/profile-page",
            "type": "text/html",
            "href": "https://example.org/@someuser",
        },
        {
            "rel": "self",
            "type": "application/activity+json",
            "href": "https://example.org/users/someuser",
        },
        {
            "rel": "http://ostatus.org/schema/1.0/subscribe",
            "template": "https://example.org/authorize_interaction?uri={uri}",
        },
    ],
}
WEBFINGER_DATA = json.dumps(WEBFINGER_VALUE).encode()

ACTOR_URL = "https://example.org/users/someuser"
ACTOR_VALUE = {
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        "https://w3id.org/security/v1",
        {
            "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
            "toot": "http://joinmastodon.org/ns#",
            "featured": {"@id": "toot:featured", "@type": "@id"},
            "alsoKnownAs": {"@id": "as:alsoKnownAs", "@type": "@id"},
            "movedTo": {"@id": "as:movedTo", "@type": "@id"},
            "schema": "http://schema.org#",
            "PropertyValue": "schema:PropertyValue",
            "value": "schema:value",
            "IdentityProof": "toot:IdentityProof",
            "discoverable": "toot:discoverable",
            "Emoji": "toot:Emoji",
            "focalPoint": {"@container": "@list", "@id": "toot:focalPoint"},
        },
    ],
    "id": "https://example.org/users/someuser",
    "type": "Person",
    "following": "https://example.org/users/someuser/following",
    "followers": "https://example.org/users/someuser/followers",
    "inbox": "https://example.org/users/someuser/inbox",
    "outbox": "https://example.org/users/someuser/outbox",
    "featured": "https://example.org/users/someuser/collections/featured",
    "preferredUsername": "someuser",
    "name": "someuser",
    "summary": "<p>My Biography</p>",
    "url": "https://example.org/@someuser",
    "manuallyApprovesFollowers": False,
    "discoverable": True,
    "publicKey": {
        "id": "https://example.org/users/someuser#main-key",
        "owner": "https://example.org/users/someuser",
        "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkaY84E/OjpjF7Dgy/nC+\nySBCiQvSOKBpNl468XP1QiOiMsILC1ec2J+LpU1Tm0kAC+uY8budLx6Wt+oz+4FU\n/82S9j9jVkWPiNVHJSQHXi13F9YQ4+MwC8niKc+qsmKUL8crSbd7dmCnOBxhvJWf\nfwOk1TW4u1fxXqHMFuw5zdfDlmRlU2FLX1LYTOxLnGp/ef/BAykV3rz6VouhAQwO\nhRay7ZgI5zlT7NtCoA17I8YiYfEs7MH0nBMrKOMw5eR1WDf5Gw78C/IAZHP1WVMv\n63V3N71OrMSfCH20OZ1H2Gyov5GX4+NSx7HI26dMDldQWOb2rYS9d0/7qM2xNUK8\n3wIDAQAB\n-----END PUBLIC KEY-----\n",
    },
    "attachment": [
        {"type": "PropertyValue", "name": "Pronoun", "value": "they"},
        {"type": "PropertyValue", "name": "Location", "value": "Somewhere"},
    ],
    "endpoints": {"sharedInbox": "https://example.org/inbox"},
    "icon": {
        "type": "Image",
        "mediaType": "image/png",
        "url": "https://assets.example.org/avatar.png",
    },
    "image": {
        "type": "Image",
        "mediaType": "image/png",
        "url": "https://assets.example.org/header.png",
    },
}
ACTOR_DATA = json.dumps(ACTOR_VALUE).encode()

OUTBOX_URL = "https://example.org/users/someuser/outbox"
OUTBOX_VALUE = {
    "@context": "https://www.w3.org/ns/activitystreams",
    "id": "https://example.org/users/someuser/outbox",
    "type": "OrderedCollection",
    "totalItems": 4835,
    "first": "https://example.org/users/someuser/outbox?page=true",
    "last": "https://example.org/users/someuser/outbox?min_id=0&page=true",
}
OUTBOX_DATA = json.dumps(OUTBOX_VALUE).encode()

OUTBOX_FIRSTPAGE_URL = "https://example.org/users/someuser/outbox?page=true"
OUTBOX_FIRSTPAGE_VALUE = {
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        {
            "ostatus": "http://ostatus.org#",
            "atomUri": "ostatus:atomUri",
            "inReplyToAtomUri": "ostatus:inReplyToAtomUri",
            "conversation": "ostatus:conversation",
            "sensitive": "as:sensitive",
            "toot": "http://joinmastodon.org/ns#",
            "votersCount": "toot:votersCount",
            "Emoji": "toot:Emoji",
            "focalPoint": {"@container": "@list", "@id": "toot:focalPoint"},
        },
    ],
    "id": "https://example.org/users/someuser/outbox?page=true",
    "type": "OrderedCollectionPage",
    "next": "https://example.org/users/someuser/outbox?max_id=104101144953797529&page=true",
    "prev": "https://example.org/users/someuser/outbox?min_id=104135036335976677&page=true",
    "partOf": "https://example.org/users/someuser/outbox",
    "orderedItems": [
        {
            "id": "https://example.org/users/someuser/statuses/104135036335976677/activity",
            "type": "Create",
            "actor": "https://example.org/users/someuser",
            "published": "2020-05-08T01:23:45Z",
            "to": ["https://example.org/users/someuser/followers"],
            "cc": [
                "https://www.w3.org/ns/activitystreams#Public",
                "https://example.com/users/FirstAuthor",
            ],
            "object": {
                "id": "https://example.org/users/someuser/statuses/1234",
                "type": "Note",
                "summary": None,
                "inReplyTo": "https://example.com/users/FirstAuthor/statuses/42",
                "published": "2020-05-08T01:23:45Z",
                "url": "https://example.org/@FirstAuthor/42",
                "attributedTo": "https://example.org/users/someuser",
                "to": ["https://example.org/users/someuser/followers"],
                "cc": [
                    "https://www.w3.org/ns/activitystreams#Public",
                    "https://example.com/users/FirstAuthor",
                ],
                "sensitive": False,
                "atomUri": "https://example.org/users/someuser/statuses/1234",
                "inReplyToAtomUri": "https://example.com/users/FirstAuthor/statuses/42",
                "conversation": "tag:example.com,2020-05-08:objectId=aaaa:objectType=Conversation",
                "content": '<p><span class="h-card"><a href="https://example.com/@FirstAuthor" class="u-url mention">@<span>FirstAuthor</span></a></span> I am replying to you</p>',
                "contentMap": {
                    "en": '<p><span class="h-card"><a href="https://example.com/@FirstAuthor" class="u-url mention">@<span>FirstAuthor</span></a></span> I am replying to you</p>'
                },
                "attachment": [],
                "tag": [
                    {
                        "type": "Mention",
                        "href": "https://example.com/users/FirstAuthor",
                        "name": "@FirstAuthor@example.com",
                    }
                ],
                "replies": {
                    "id": "https://example.org/users/someuser/statuses/1234/replies",
                    "type": "Collection",
                    "first": {
                        "type": "CollectionPage",
                        "next": "https://example.org/users/someuser/statuses/1234/replies?only_other_accounts=true&page=true",
                        "partOf": "https://example.org/users/someuser/statuses/1234/replies",
                        "items": [],
                    },
                },
            },
        },
        {
            "id": "https://example.org/users/someuser/statuses/12345/activity",
            "type": "Announce",
            "actor": "https://example.org/users/someuser",
            "published": "2020-05-05T11:22:33Z",
            "to": ["https://example.org/users/someuser/followers"],
            "cc": [
                "https://example.net/users/BoostedUser",
                "https://www.w3.org/ns/activitystreams#Public",
            ],
            "object": "https://example.net/users/BoostedUser/statuses/123456",
            "atomUri": "https://example.org/users/someuser/statuses/12345/activity",
        },
    ],
}
OUTBOX_FIRSTPAGE_DATA = json.dumps(OUTBOX_FIRSTPAGE_VALUE).encode()

BOOSTED_URL = "https://example.net/users/BoostedUser/statuses/123456"
BOOSTED_VALUE = {
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        {
            "ostatus": "http://ostatus.org#",
            "atomUri": "ostatus:atomUri",
            "inReplyToAtomUri": "ostatus:inReplyToAtomUri",
            "conversation": "ostatus:conversation",
            "sensitive": "as:sensitive",
            "toot": "http://joinmastodon.org/ns#",
            "votersCount": "toot:votersCount",
            "blurhash": "toot:blurhash",
            "focalPoint": {"@container": "@list", "@id": "toot:focalPoint"},
        },
    ],
    "id": "https://example.net/users/BoostedUser/statuses/123456",
    "type": "Note",
    "summary": None,
    "inReplyTo": None,
    "published": "2020-05-05T11:00:00Z",
    "url": "https://example.net/@BoostedUser/123456",
    "attributedTo": "https://example.net/users/BoostedUser",
    "to": ["https://www.w3.org/ns/activitystreams#Public"],
    "cc": ["https://example.net/users/BoostedUser/followers"],
    "sensitive": False,
    "atomUri": "https://example.net/users/BoostedUser/statuses/123456",
    "inReplyToAtomUri": None,
    "conversation": "tag:example.net,2020-05-05:objectId=bbbbb:objectType=Conversation",
    "content": "<p>Status Content</p>",
    "contentMap": {"en": "<p>Status Content</p>"},
    "attachment": [
        {
            "type": "Document",
            "mediaType": "image/png",
            "url": "https://example.net/system/media_attachments/image.png",
            "name": "Alt Text",
            "focalPoint": [0.0, 0.0],
        }
    ],
    "tag": [],
    "replies": {
        "id": "https://example.net/users/BoostedUser/statuses/123456/replies",
        "type": "Collection",
        "first": {
            "type": "CollectionPage",
            "next": "https://example.net/users/BoostedUser/statuses/123456/replies?only_other_accounts=true&page=true",
            "partOf": "https://example.net/users/BoostedUser/statuses/123456/replies",
            "items": [],
        },
    },
}
BOOSTED_DATA = json.dumps(BOOSTED_VALUE).encode()

BOOSTED_ACTOR_URL = "https://example.net/users/BoostedUser"
BOOSTED_ACTOR_VALUE = {
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        "https://w3id.org/security/v1",
        {
            "manuallyApprovesFollowers": "as:manuallyApprovesFollowers",
            "toot": "http://joinmastodon.org/ns#",
            "featured": {"@id": "toot:featured", "@type": "@id"},
            "alsoKnownAs": {"@id": "as:alsoKnownAs", "@type": "@id"},
            "movedTo": {"@id": "as:movedTo", "@type": "@id"},
            "schema": "http://schema.org#",
            "PropertyValue": "schema:PropertyValue",
            "value": "schema:value",
            "IdentityProof": "toot:IdentityProof",
            "discoverable": "toot:discoverable",
            "focalPoint": {"@container": "@list", "@id": "toot:focalPoint"},
        },
    ],
    "id": "https://example.net/users/BoostedUser",
    "type": "Person",
    "following": "https://example.net/users/BoostedUser/following",
    "followers": "https://example.net/users/BoostedUser/followers",
    "inbox": "https://example.net/users/BoostedUser/inbox",
    "outbox": "https://example.net/users/BoostedUser/outbox",
    "featured": "https://example.net/users/BoostedUser/collections/featured",
    "preferredUsername": "BoostedUser",
    "name": "Boosted User",
    "url": "https://example.net/@BoostedUser",
    "endpoints": {"sharedInbox": "https://example.net/inbox"},
}
BOOSTED_ACTOR_DATA = json.dumps(BOOSTED_ACTOR_VALUE).encode()


class FediverseTestCase(ChannelPluginTestCase):
    plugins = ("Fediverse",)

    def setUp(self):
        super().setUp()
        path = conf.supybot.directories.data.dirize(
            "Fediverse/instance_key.pem"
        )
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fd:
            fd.write(PRIVATE_KEY)

    @contextlib.contextmanager
    def mockRequests(self, expected_requests):
        with Manager() as m:
            expected_requests = m.list(expected_requests)
            original_getUrlContent = utils.web.getUrlContent

            @functools.wraps(original_getUrlContent)
            def newf(url, headers={}, data=None):
                self.assertIsNone(data, "Unexpected POST")
                assert expected_requests, url
                (expected_url, response) = expected_requests.pop(0)
                self.assertEqual(url, expected_url, "Unexpected URL")

                if isinstance(response, bytes):
                    return response
                elif isinstance(response, Exception):
                    raise response
                else:
                    assert False, response

            utils.web.getUrlContent = newf

            try:
                yield
            finally:
                utils.web.getUrlContent = original_getUrlContent

            self.assertEqual(
                list(expected_requests), [], "Less requests than expected."
            )

    if network:

        def testNetworkProfile(self):
            self.assertRegexp("profile @val@oc.todon.fr", "0E082B40E4376B1E")
            # TODO: add a test with an instance which only allows fetches
            # with valid signatures.

        def testNetworkProfileUnknown(self):
            self.assertResponse(
                "profile @nonexistinguser@oc.todon.fr",
                "Error: Unknown user @nonexistinguser@oc.todon.fr.",
            )

    def testFeaturedNone(self):
        featured = {
            "@context": "https://www.w3.org/ns/activitystreams",
            "id": "https://example.org/users/someuser/collections/featured",
            "type": "OrderedCollection",
            "orderedItems": [],
        }
        expected_requests = [
            (HOSTMETA_URL, HOSTMETA_DATA),
            (WEBFINGER_URL, WEBFINGER_DATA),
            (ACTOR_URL, ACTOR_DATA),
            (
                "https://example.org/users/someuser/collections/featured",
                json.dumps(featured).encode(),
            ),
        ]
        with self.mockRequests(expected_requests):
            self.assertResponse(
                "featured @someuser@example.org", "No featured statuses."
            )

    def testFeaturedSome(self):
        featured = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                {
                    "ostatus": "http://ostatus.org#",
                    "atomUri": "ostatus:atomUri",
                    "inReplyToAtomUri": "ostatus:inReplyToAtomUri",
                    "conversation": "ostatus:conversation",
                    "sensitive": "as:sensitive",
                    "toot": "http://joinmastodon.org/ns#",
                    "votersCount": "toot:votersCount",
                },
            ],
            "id": "https://example.org/users/someuser/collections/featured",
            "type": "OrderedCollection",
            "orderedItems": [
                {
                    "id": "https://example.org/users/someuser/statuses/123456789",
                    "type": "Note",
                    "summary": None,
                    "inReplyTo": "https://example.org/users/someuser/statuses/100543712346463856",
                    "published": "2018-08-13T15:49:00Z",
                    "url": "https://example.org/@someuser/123456789",
                    "attributedTo": "https://example.org/users/someuser",
                    "to": ["https://example.org/users/someuser/followers"],
                    "cc": ["https://www.w3.org/ns/activitystreams#Public"],
                    "sensitive": False,
                    "atomUri": "https://example.org/users/someuser/statuses/123456789",
                    "inReplyToAtomUri": "https://example.org/users/someuser/statuses/100543712346463856",
                    "conversation": "tag:example.org,2018-08-13:objectId=3002048:objectType=Conversation",
                    "content": "<p>This is a pinned toot</p>",
                    "contentMap": {"en": "<p>This is a pinned toot</p>"},
                    "attachment": [],
                    "tag": [],
                    "replies": {
                        "id": "https://example.org/users/someuser/statuses/123456789/replies",
                        "type": "Collection",
                        "first": {
                            "type": "CollectionPage",
                            "next": "https://example.org/users/someuser/statuses/123456789/replies?min_id=100723569923690076&page=true",
                            "partOf": "https://example.org/users/someuser/statuses/123456789/replies",
                            "items": [
                                "https://example.org/users/someuser/statuses/100723569923690076"
                            ],
                        },
                    },
                }
            ],
        }

        expected_requests = [
            (HOSTMETA_URL, HOSTMETA_DATA),
            (WEBFINGER_URL, WEBFINGER_DATA),
            (ACTOR_URL, ACTOR_DATA),
            (
                "https://example.org/users/someuser/collections/featured",
                json.dumps(featured).encode(),
            ),
        ]

        with self.mockRequests(expected_requests):
            self.assertRegexp(
                "featured @someuser@example.org", "This is a pinned toot"
            )

    def testProfile(self):
        expected_requests = [
            (HOSTMETA_URL, HOSTMETA_DATA),
            (WEBFINGER_URL, WEBFINGER_DATA),
            (ACTOR_URL, ACTOR_DATA),
        ]

        with self.mockRequests(expected_requests):
            self.assertResponse(
                "profile @someuser@example.org",
                "\x02someuser\x02 (@someuser@example.org): My Biography",
            )

    def testProfileSnarfer(self):
        with conf.supybot.plugins.Fediverse.usernameSnarfer.context(True):
            expected_requests = [
                (HOSTMETA_URL, HOSTMETA_DATA),
                (WEBFINGER_URL, WEBFINGER_DATA),
                (ACTOR_URL, ACTOR_DATA),
            ]

            with self.mockRequests(expected_requests):
                self.assertSnarfResponse(
                    "aaa @someuser@example.org bbb",
                    "\x02someuser\x02 (@someuser@example.org): My Biography",
                )

            expected_requests = [
                (HOSTMETA_URL, HOSTMETA_DATA),
                (WEBFINGER_URL, utils.web.Error("blah")),
            ]

            with self.mockRequests(expected_requests):
                self.assertSnarfNoResponse(
                    "aaa @nonexistinguser@example.org bbb", timeout=1
                )

    def testProfileUnknown(self):
        expected_requests = [
            (HOSTMETA_URL, HOSTMETA_DATA),
            (WEBFINGER_URL, utils.web.Error("blah")),
        ]

        with self.mockRequests(expected_requests):
            self.assertResponse(
                "profile @nonexistinguser@example.org",
                "Error: Unknown user @nonexistinguser@example.org.",
            )

    def testStatuses(self):
        expected_requests = [
            (HOSTMETA_URL, HOSTMETA_DATA),
            (WEBFINGER_URL, WEBFINGER_DATA),
            (ACTOR_URL, ACTOR_DATA),
            (OUTBOX_URL, OUTBOX_DATA),
            (OUTBOX_FIRSTPAGE_URL, OUTBOX_FIRSTPAGE_DATA),
            (BOOSTED_URL, BOOSTED_DATA),
            (BOOSTED_ACTOR_URL, BOOSTED_ACTOR_DATA),
        ]

        with self.mockRequests(expected_requests):
            self.assertResponse(
                "statuses @someuser@example.org",
                "\x02someuser (@someuser@example.org)\x02: "
                + "@ FirstAuthor I am replying to you and "
                + "\x02Boosted User (@BoostedUser@example.net)\x02: "
                + "Status Content",
            )


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
