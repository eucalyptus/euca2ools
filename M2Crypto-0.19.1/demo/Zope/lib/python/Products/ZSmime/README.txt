ZSmime enables Zope to generate S/MIME-signed/encrypted messages.

ZSmime is useful where Zope accepts confidential information over the
web, e.g., credit card information, Swiss bank account instructions, etc. 
Such information can be protected by ZSmime and relayed off-site 
immediately. This reduces the value of the information carried on-site
and in turn reduces the effect of a successful attack against the site.

Even if the S/MIME-protected information remains on-site, it is now 
encrypted - this introduces additional cost in defeating the protection 
and may mitigate the impact of a successful site penetration.

ZSmime adds a DTML tag "dtml-smime" to Zope. 


$Id: README.txt 299 2005-06-09 17:32:28Z heikki $
$Revision: 1.1 $

