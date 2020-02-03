import base64
from datetime import datetime

from django.test import testcases

from conf import colours, settings


class LiteHMRCTestClient(testcases.TestCase):
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        if settings.TIME_TESTS:
            self.tick = datetime.now()

        self.licence_usage_file_name = "ILBDOTI_live_CHIEF_usageData_9876_201901130300"
        string = r"""1\fileHeader\CHIEF\SPIRE\usageData\201901130300\9876\
        2\licenceUsage\LU04148/00001\insert\GBOIE2017/12345B\O\
        3\line\1\0\0\
        4\usage\O\9GB000001328000-PE112345\R\20190112\0\0\\000262\\\\
        5\usage\O\9GB000001328000-PE112345\L\20190112\0\0\\000262\\\\
        6\usage\O\9GB000001328000-PE112345\K\20190112\0\0\\000262\\\\
        7\end\line\5
        8\end\licenceUsage\7
        9\licenceUsage\LU04148/00002\insert\GBOGE2014/23456\O\
        10\line\1\0\0\
        11\usage\O\9GB000003133000-445251012345\Z\20190112\0\0\\000962\\\\
        12\end\line\3
        13\end\licenceUsage\5
        14\licenceUsage\LU04148/00003\insert\GBOGE2018/34567\O\
        15\line\1\0\0\
        16\usage\O\9GB000001328000-PE112345\A\20190112\0\0\\000442\\\\
        17\end\line\3
        18\end\licenceUsage\5
        19\licenceUsage\LU04148/00004\insert\GBSIE2018/45678\O\
        20\line\1\3\0\
        21\usage\O\9GB00000133000-774170812345\D\20190112\3\0\\009606\\\\
        22\end\line\3
        23\end\licenceUsage\5
        24\licenceUsage\LU04148/00005\insert\GBOGE2011/56789\O\
        25\line\1\0\0\
        26\usage\O\9GB000004988000-4750437112345\G\20190111\0\0\\000104\\\\
        27\usage\O\9GB000004988000-4750436912345\Y\20190111\0\0\\000104\\\\
        28\end\line\4
        29\end\licenceUsage\6
        30\licenceUsage\LU04148/00006\insert\GBOGE2017/98765\O\
        31\line\1\0\0\
        32\usage\O\9GB000002816000-273993\L\20190109\0\0\\000316\\\\
        33\end\line\3
        34\end\licenceUsage\5
        35\licenceUsage\LU04148/00007\insert\GBOGE2015/87654\O\
        36\line\1\0\0\
        37\usage\O\9GB000003133000-784920212345\E\20190111\0\0\\000640\\\\
        38\usage\O\9GB000003133000-784918012345\D\20190111\0\0\\000640\\\\
        39\end\line\4
        40\end\licenceUsage\6
        41\fileTrailer\7"""
        self.licence_usage_file_body = string.encode("utf-8")

        self.licence_update_reply_body = """
MVxmaWxlSGVhZGVyXENISUVGXFNQSVJFXGxpY2VuY2VSZXBseVwyMDE5MDIwODAwMjVcNDk1NDMg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAKMlxhY2NlcHRlZFwyNTYzOTkgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKM1xmaWxlVHJhaWxlclwxXDBcMCAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg
ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAK"""
        self.licence_update_reply_name = (
            "ILBDOTI_live_CHIEF_licenceReply_49543_201902080025"
        )

        self.usage_update_reply_name = (
            "ILBDOTI_live_CHIEF_usageReply_49543_201902080025"
        )

        self.licence_update_file_name = (
            "ILBDOTI_live_CHIEF_licenceUpdate_49543_201902080025"
        )

    def tearDown(self):
        """
        Print output time for tests if settings.TIME_TESTS is set to True
        """
        if settings.TIME_TESTS:
            self.tock = datetime.now()

            diff = self.tock - self.tick
            time = round(diff.microseconds / 1000, 2)
            colour = colours.green
            emoji = ""

            if time > 100:
                colour = colours.orange
            if time > 300:
                colour = colours.red
                emoji = " 🔥"

            print(self._testMethodName + emoji + " " + colour(str(time) + "ms") + emoji)


r"""Return-Path: <spirechiefops@spiretest.trade.gov.uk>
Delivered-To: incoming@tpg.service.dev.uktrade.io
Received: from tpg.service.dev.uktrade.io
	by f9dffa2fa531 with LMTP
	id Uh8OBQj1Ml7ONAAA9BQ3Lw
	(envelope-from <spirechiefops@spiretest.trade.gov.uk>)
	for <incoming@tpg.service.dev.uktrade.io>; Thu, 30 Jan 2020 15:23:52 +0000
Received: from mail1.spiretest.trade.gov.uk (unknown [51.179.210.216])
	by tpg.service.dev.uktrade.io (Postfix) with ESMTPS id 0F585C03B2
	for <incoming@tpg.service.dev.uktrade.io>; Thu, 30 Jan 2020 15:23:52 +0000 (UTC)
Received: from localhost (unknown [10.0.0.2])
	by mail1.spiretest.trade.gov.uk (Postfix) with ESMTP id 72EE840A724
	for <incoming@tpg.service.dev.uktrade.io>; Thu, 30 Jan 2020 15:23:51 +0000 (GMT)
Date: Thu, 30 Jan 2020 15:23:51 +0000
From: spirechiefops@spiretest.trade.gov.uk
To: incoming@tpg.service.dev.uktrade.io
Subject: Test to LITE from SPIRE with attachement
Message-ID: <20200130152351.00003e74@fivium.co.uk>
X-Mailer: Claws Mail 3.17.4 (GTK+ 2.24.32; i686-w64-mingw32)
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="MP_/BB7GcXYKYL=fbUxj1xinQYI"
--MP_/BB7GcXYKYL=fbUxj1xinQYI
Content-Type: text/plain; charset=US-ASCII
Content-Transfer-Encoding: 7bit
Content-Disposition: inline
This is a test mail, please ignore.
--MP_/BB7GcXYKYL=fbUxj1xinQYI
Content-Type: text/plain
Content-Transfer-Encoding: 7bit
Content-Disposition: attachment; filename=test_attachement.txt
TG9yZW0gSXBzdW0gaXMgc2ltcGx5IGR1bW15IHRleHQgb2YgdGhlIHByaW50aW5nIGFuZCB0eXBlc2V0dGluZyBpbmR1c3RyeS4gTG9yZW0gSXBzdW0gaGFzIGJlZW4gdGhlIGluZHVzdHJ5J3Mgc3RhbmRhcmQgZHVtbXkgdGV4dCBldmVyIHNpbmNlIHRoZSAxNTAwcywgd2hlbiBhbiB1bmtub3duIHByaW50ZXIgdG9vayBhIGdhbGxleSBvZiB0eXBlIGFuZCBzY3JhbWJsZWQgaXQgdG8gbWFrZSBhIHR5cGUgc3BlY2ltZW4gYm9vay4gSXQgaGFzIHN1cnZpdmVkIG5vdCBvbmx5IGZpdmUgY2VudHVyaWVzLCBidXQgYWxzbyB0aGUgbGVhcCBpbnRvIGVsZWN0cm9uaWMgdHlwZXNldHRpbmcsIHJlbWFpbmluZyBlc3NlbnRpYWxseSB1bmNoYW5nZWQuIEl0IHdhcyBwb3B1bGFyaXNlZCBpbiB0aGUgMTk2MHMgd2l0aCB0aGUgcmVsZWFzZSBvZiBMZXRyYXNldCBzaGVldHMgY29udGFpbmluZyBMb3JlbSBJcHN1bSBwYXNzYWdlcywgYW5kIG1vcmUgcmVjZW50bHkgd2l0aCBkZXNrdG9wIHB1Ymxpc2hpbmcgc29mdHdhcmUgbGlrZSBBbGR1cyBQYWdlTWFrZXIgaW5jbHVkaW5nIHZlcnNpb25zIG9mIExvcmVtIElwc3VtLg==
--MP_/BB7GcXYKYL=fbUxj1xinQYI--"""
