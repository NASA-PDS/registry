## How Tos

### How do I track down a missing LDD.json file needed by the registry?
Getting this error, what do I do?

```
[INFO] 404 - Not Found
[INFO] Will retry in 5 seconds
[INFO] Downloading https://urldefense.us/v3/__https://pds.nasa.gov/pds4/mission/cassini/v1/PDS4_CASSINI_1D00_1500.JSON__;!!PvBDto6Hs4WbVuu7!PmT82InBdXvS96orrqX3dZ7dmffUFgnIdzMrbUnIpfNFAOwt8q-WPJ4ZAoLFWJLjzGkeNsGYjpU5X6OvyxhI2EWS3XuT$ <https://urldefense.us/v3/__https://pds.nasa.gov/pds4/mission/cassini/v1/PDS4_CASSINI_1D00_1500.JSON__;!!PvBDto6Hs4WbVuu7!PmT82InBdXvS96orrqX3dZ7dmffUFgnIdzMrbUnIpfNFAOwt8q-WPJ4ZAoLFWJLjzGkeNsGYjpU5X6OvyxhI2EWS3XuT$> to /tmp/LDD-12896839279374442894.JSON
Nov 19, 2024 8:54:43 AM org.apache.http.client.protocol.ResponseProcessCookies processCookies
WARNING: Invalid cookie header: "Set-Cookie: AWSALB=+AZDT/Dyrlyf8qjBZAO7AS3ZGSz35DYAWwxGQZpyH2y+6rvu9PYeyoDJIzWALA9F5SHbhBMTnBBAXTsijaHOU98DE9A2Mt73BWHSPwbOHrcIV63WkPfXQaCRsxrF; Expires=Tue, 26 Nov 2024 16:54:43 GMT; Path=/". Invalid 'expires' attribute: Tue, 26 Nov 2024 16:54:43 GMT
Nov 19, 2024 8:54:43 AM org.apache.http.client.protocol.ResponseProcessCookies processCookies
WARNING: Invalid cookie header: "Set-Cookie: AWSALBCORS=+AZDT/Dyrlyf8qjBZAO7AS3ZGSz35DYAWwxGQZpyH2y+6rvu9PYeyoDJIzWALA9F5SHbhBMTnBBAXTsijaHOU98DE9A2Mt73BWHSPwbOHrcIV63WkPfXQaCRsxrF; Expires=Tue, 26 Nov 2024 16:54:43 GMT; Path=/; SameSite=None; Secure". Invalid 'expires' attribute: Tue, 26 Nov 2024 16:54:43 GMT
[INFO] 404 - Not Found
```

Note the version of the LDD, since that is very important. For the example above `PDS4_CASSINI_1D00_1500.JSON`, indicates we need the PDS4 Cassini LDD v1.5.0.0 built with PDS4 IM 1D00.

1. First, check the ldd repository history to see if the version already exists and just needs to be released: https://github.com/pds-data-dictionaries/ldd-cassini/releases
2. If it does exist as a GitHub release, post to [portal-legacy repo](https://github.com/NASA-PDS/portal-legacy/tree/main/datastandards/schema/released) develop branch, and create pull request to be merged to main.
3. If it does exist as a GitHub release, look in [portal-legacy repo](https://github.com/NASA-PDS/portal-legacy/tree/main/datastandards/schema/released) to see if an older version of the IngestLDD exists.
4. If you find an older version of the IngestLDD in portal-legacy, add to the LDD repository, and run LDDTool to generate the JSON: `lddtool -lpJm input_historical_ingestldd.xml`
5. Post to [portal-legacy repo](https://github.com/NASA-PDS/portal-legacy/tree/main/datastandards/schema/released) develop branch, and create pull request to be merged to main.

