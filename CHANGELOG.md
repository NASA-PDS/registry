# Changelog

## [«unknown»](https://github.com/NASA-PDS/registry/tree/«unknown») (2023-04-17)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.3...«unknown»)

**Requirements:**

- As a user, I want to all metadata attributes to be searchable [\#153](https://github.com/NASA-PDS/registry/issues/153)
- As a user, I want to view dashboard report of bundles with archive status and other tracking information [\#130](https://github.com/NASA-PDS/registry/issues/130)
- Update documentation to include explicit example of how to query staged data [\#100](https://github.com/NASA-PDS/registry/issues/100)
- As a user, I want to indicate a product has been superseded [\#52](https://github.com/NASA-PDS/registry/issues/52)

**Improvements:**

- Update docs to be more clear that there is a required next step after data ingestion [\#139](https://github.com/NASA-PDS/registry/issues/139)

**Defects:**

- Expo system doesn't use latest images published to Docker Hub [\#175](https://github.com/NASA-PDS/registry/issues/175)
- ref\_collection\_lidvid field in some node registries populated using older versions of registry loader tools create string fields in the schema vs. the expected list types [\#159](https://github.com/NASA-PDS/registry/issues/159) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- TLS termination listening on wrong port [\#150](https://github.com/NASA-PDS/registry/issues/150) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- Expo Registry fails to start [\#149](https://github.com/NASA-PDS/registry/issues/149) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- OpenSearch service of Registry won't start on Linux [\#146](https://github.com/NASA-PDS/registry/issues/146) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Harvest is throwing errors of "Forbidden index write" [\#132](https://github.com/NASA-PDS/registry/issues/132) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- registry-manager won't set archive-status on some collections [\#97](https://github.com/NASA-PDS/registry/issues/97) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]

**Other closed issues:**

- Update Terraform scripts to support multi-tenancy [\#188](https://github.com/NASA-PDS/registry/issues/188)
- Check that none of the Opensearch servers, besides NAIF have archive\_status==null [\#183](https://github.com/NASA-PDS/registry/issues/183)
- Add documentation on the auth.cfg file for the registry tools users [\#170](https://github.com/NASA-PDS/registry/issues/170)
- Schedule provenance script [\#160](https://github.com/NASA-PDS/registry/issues/160)
- Integrate new `provenance.py` script into operational deployment to tag products with Provenance information [\#141](https://github.com/NASA-PDS/registry/issues/141)
- Integrate new `provenance.py` script into integration tests to tag products with Provenance information [\#140](https://github.com/NASA-PDS/registry/issues/140)

## [v1.1.3](https://github.com/NASA-PDS/registry/tree/v1.1.3) (2022-12-14)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.2...v1.1.3)

**Defects:**

- follow on to \#118, registry-manager still unable to change archive status on bundle contents [\#136](https://github.com/NASA-PDS/registry/issues/136) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- archive status value was not changed on bundle's contents [\#118](https://github.com/NASA-PDS/registry/issues/118) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]

## [v1.1.2](https://github.com/NASA-PDS/registry/tree/v1.1.2) (2022-11-10)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.1...v1.1.2)

## [v1.1.1](https://github.com/NASA-PDS/registry/tree/v1.1.1) (2022-10-26)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.0...v1.1.1)

**Defects:**

- Continuous Delivery not working with OpenSearch [\#120](https://github.com/NASA-PDS/registry/issues/120) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]

## [v1.1.0](https://github.com/NASA-PDS/registry/tree/v1.1.0) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.2...v1.1.0)

**Defects:**

- Missing INSIGHT LDD v1600 [\#84](https://github.com/NASA-PDS/registry/issues/84) [[s.low](https://github.com/NASA-PDS/registry/labels/s.low)]

## [v1.0.2](https://github.com/NASA-PDS/registry/tree/v1.0.2) (2022-08-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.1...v1.0.2)

**Defects:**

- when docker compose starts, registry-api docker is missing curl [\#69](https://github.com/NASA-PDS/registry/issues/69) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Scalable Harvest does not replace file paths with the appropriate URL prefix [\#64](https://github.com/NASA-PDS/registry/issues/64) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- docker compose int-registry-batch-loader failure [\#41](https://github.com/NASA-PDS/registry/issues/41) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]

**Other closed issues:**

- Update README to reflect best practices of other PDS repositories [\#53](https://github.com/NASA-PDS/registry/issues/53) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Develop script to update existing registry metadata per B12.1 metadata modifications [\#43](https://github.com/NASA-PDS/registry/issues/43)
- Plan and strategize how to migrate to OpenSearch deployments [\#54](https://github.com/NASA-PDS/registry/issues/54)
- Add supersede / update product version functionality in Registry Manager [\#56](https://github.com/NASA-PDS/registry/issues/56)
- Add new "alternate\_ids" field to Elasticsearch schema [\#59](https://github.com/NASA-PDS/registry/issues/59)
- Design the PDS4 definition for describing superseded LIDs via product metadata [\#57](https://github.com/NASA-PDS/registry/issues/57)

## [v1.0.1](https://github.com/NASA-PDS/registry/tree/v1.0.1) (2022-05-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.0...v1.0.1)

## [v1.0.0](https://github.com/NASA-PDS/registry/tree/v1.0.0) (2022-05-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.0-SNAPSHOT...v1.0.0)

**Requirements:**

- Upgrade the initialization of the ES/OS database following latest upgrade of components [\#31](https://github.com/NASA-PDS/registry/issues/31)
- As a user, I want to switch a bundle and it's associated collections and products from a protected status to operational. [\#105](https://github.com/NASA-PDS/registry/issues/105)
- As a user, I want to change the archive status for a collection and it's associated products [\#115](https://github.com/NASA-PDS/registry/issues/115)

## [v1.0.0-SNAPSHOT](https://github.com/NASA-PDS/registry/tree/v1.0.0-SNAPSHOT) (2022-01-20)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/1f4d45e5a395b8d05b58a0924066dcd3cd0b3565...v1.0.0-SNAPSHOT)

**Requirements:**

- As a node operator, I want the the registry schema to update autonomously when new data is ingested. [\#113](https://github.com/NASA-PDS/registry/issues/113)
- As a developer, I want to include supplemental file data sizes in the registry [\#112](https://github.com/NASA-PDS/registry/issues/112)
- As a node operator, I want to ingest metadata regarding secondary collections that belong to a bundle. [\#109](https://github.com/NASA-PDS/registry/issues/109)
- As a node operator, I want to ingest metadata regarding secondary products that belong to a collection. [\#108](https://github.com/NASA-PDS/registry/issues/108)
- As a node operator, I want actionable, user-friendly error messages for registry schema failures [\#110](https://github.com/NASA-PDS/registry/issues/110)
- The service shall allow deletion of registered artifacts [\#103](https://github.com/NASA-PDS/registry/issues/103)
- The service shall provide a means identifying relationships between artifact registrations [\#104](https://github.com/NASA-PDS/registry/issues/104)
- As a registry user, I want to ingest supplemental metadata from Product\_Metadata\_Supplemental. [\#121](https://github.com/NASA-PDS/registry/issues/121)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
