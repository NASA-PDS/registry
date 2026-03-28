# Planetary Data System API Reference Tests Copy 14

Federated PDS API which provides actionable end points standardized
between the different nodes.


Contact Support:
 Email: pds-operator@jpl.nasa.gov

> Auto-generated from `postman_collection.json`. Do not edit manually.


## Table of Contents

- [cookbook examples](#cookbook-examples)
  - [`GET`] [Latest lidvid for a given lid (no suffix))](#latest-lidvid-for-a-given-lid-no-suffix)
  - [`GET`] [Latest lidvid for a given lid (latest suffix)](#latest-lidvid-for-a-given-lid-latest-suffix)
  - [`GET`] [All lidvid for a given lid (all suffix)](#all-lidvid-for-a-given-lid-all-suffix)
  - [`GET`] [Search by processing level](#search-by-processing-level)
  - [`GET`] [Search by target](#search-by-target)
  - [`GET`] [Search by reference](#search-by-reference)
  - [`GET`] [search for collection of an observtional product, kvp response](#search-for-collection-of-an-observtional-product-kvp-response)
  - [`GET`] [Search for a product knowing its DOI](#search-for-a-product-knowing-its-doi)
- [requirements](#requirements)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports EQ](#nasa-pdsregistry-api494-querystring-supports-eq)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports NE](#nasa-pdsregistry-api494-querystring-supports-ne)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports GT](#nasa-pdsregistry-api494-querystring-supports-gt)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports LT](#nasa-pdsregistry-api494-querystring-supports-lt)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports GE](#nasa-pdsregistry-api494-querystring-supports-ge)
  - [`GET`] [NASA-PDS/registry-api#494 querystring supports LE](#nasa-pdsregistry-api494-querystring-supports-le)
  - [`GET`] [NASA-PDS/registry-api#495 querystring supports AND](#nasa-pdsregistry-api495-querystring-supports-and)
  - [`GET`] [NASA-PDS/registry-api#495 querystring supports OR](#nasa-pdsregistry-api495-querystring-supports-or)
  - [`GET`] [NASA-PDS/registry-api#495 querystring supports NOT](#nasa-pdsregistry-api495-querystring-supports-not)
  - [`GET`] [NASA-PDS/registry-api#493 querystring supports NOT on other endpoint](#nasa-pdsregistry-api493-querystring-supports-not-on-other-endpoint)
  - [`GET`] [NASA-PDS/registry-api#495 querystring supports lowercase operators](#nasa-pdsregistry-api495-querystring-supports-lowercase-operators)
  - [`GET`] [NASA-PDS/pds-api#72 search by a temporal range as an ISO-8601 time interval](#nasa-pdspds-api72-search-by-a-temporal-range-as-an-iso-8601-time-interval)
  - [`GET`] [NASA-PDS/pds-api#99 free text search](#nasa-pdspds-api99-free-text-search)
  - [`GET`] [NASA-PDS/registry-api#80 select fields in response for lid/lidvid resolution](#nasa-pdsregistry-api80-select-fields-in-response-for-lidlidvid-resolution)
  - [`GET`] [NASA-PDS/registry#153 all properties are searchable](#nasa-pdsregistry153-all-properties-are-searchable)
  - [`GET`] [NASA-PDS/registry-api#349 Request for json+pds4 response fails in production](#nasa-pdsregistry-api349-request-for-jsonpds4-response-fails-in-production)
  - [`GET`] [NASA-PDS/registry-api#336 As a PDS operator, I want to know the health of the registry API service](#nasa-pdsregistry-api336-as-a-pds-operator-i-want-to-know-the-health-of-the-registry-api-service)
  - [`GET`] [NASA-PDS/registry-api/352 pagination step 1](#nasa-pdsregistry-api352-pagination-step-1)
  - [`GET`] [NASA-PDS/registry-api/352 pagination step 2](#nasa-pdsregistry-api352-pagination-step-2)
  - [`GET`] [NASA-PDS/registry-api/352 members pagination step 1](#nasa-pdsregistry-api352-members-pagination-step-1)
  - [`GET`] [NASA-PDS/registry-api/352 members pagination step 2](#nasa-pdsregistry-api352-members-pagination-step-2)
  - [`GET`] [NASA-PDS/registry-api#434 get product from lidvid](#nasa-pdsregistry-api434-get-product-from-lidvid)
  - [`GET`] [NASA-PDS/registry-api#434 get product from lidvid not supported Accept](#nasa-pdsregistry-api434-get-product-from-lidvid-not-supported-accept)
  - [`GET`] [NASA-PDS/registry-api#434 get product from lidvid missing](#nasa-pdsregistry-api434-get-product-from-lidvid-missing)
  - [`GET`] [NASA-PDS/registry-api#435 get latest product from lid](#nasa-pdsregistry-api435-get-latest-product-from-lid)
  - [`GET`] [NASA-PDS/registry-api#435 get latest product from lid with explicit latest](#nasa-pdsregistry-api435-get-latest-product-from-lid-with-explicit-latest)
  - [`GET`] [NASA-PDS/registry-api#436 get all product for a given lid](#nasa-pdsregistry-api436-get-all-product-for-a-given-lid)
  - [`GET`] [NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 1](#nasa-pdsregistry-api436-get-all-product-for-a-given-lid-with-pagination-page-1)
  - [`GET`] [NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 2](#nasa-pdsregistry-api436-get-all-product-for-a-given-lid-with-pagination-page-2)
  - [`GET`] [NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 2 missing sort](#nasa-pdsregistry-api436-get-all-product-for-a-given-lid-with-pagination-page-2-missing-sort)
  - [`GET`] [NASA-PDS/registry-api#469 q param simple criteria](#nasa-pdsregistry-api469-q-param-simple-criteria)
  - [`GET`] [NASA-PDS/registry-api/issues/66 invalid q string](#nasa-pdsregistry-apiissues66-invalid-q-string)
  - [`GET`] [NASA-PDS/registry-api#457 q param like operator with wildcard](#nasa-pdsregistry-api457-q-param-like-operator-with-wildcard)
  - [`GET`] [NASA-PDS/registry-api#469 q param criteria combination](#nasa-pdsregistry-api469-q-param-criteria-combination)
  - [`GET`] [NASA-PDS/registry-api#223 products/{id}/members](#nasa-pdsregistry-api223-productsidmembers)
  - [`GET`] [NASA-PDS/registry-api#484 products/{id}/members default to latest-only](#nasa-pdsregistry-api484-productsidmembers-default-to-latest-only)
  - [`GET`] [NASA-PDS/registry-api#453 products/{id}/members/members](#nasa-pdsregistry-api453-productsidmembersmembers)
  - [`GET`] [NASA-PDS/registry-api#485 products/{id}/members/members default to latest-only](#nasa-pdsregistry-api485-productsidmembersmembers-default-to-latest-only)
  - [`GET`] [NASA-PDS/registry-api#451/452 products/{id}/member-of](#nasa-pdsregistry-api451452-productsidmember-of)
  - [`GET`] [NASA-PDS/registry-api#451/486 products/{id}/member-of default to latest-only](#nasa-pdsregistry-api451486-productsidmember-of-default-to-latest-only)
  - [`GET`] [NASA-PDS/registry-api#454 products/{id}/member-of/member-of](#nasa-pdsregistry-api454-productsidmember-ofmember-of)
  - [`GET`] [NASA-PDS/registry-api#487 products/{id}/member-of/member-of default to latest-only](#nasa-pdsregistry-api487-productsidmember-ofmember-of-default-to-latest-only)
  - [`GET`] [NASA-PDS/registry-api#497 application/json multi product result does not contain blobs](#nasa-pdsregistry-api497-applicationjson-multi-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#497 application/json single product result does not contain blobs](#nasa-pdsregistry-api497-applicationjson-single-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#497 application/kvp+json multi-product result does not contain blobs](#nasa-pdsregistry-api497-applicationkvpjson-multi-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#497 application/kvp+json single product result does not contain blobs](#nasa-pdsregistry-api497-applicationkvpjson-single-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#497 application/xml single product result does not contain blobs](#nasa-pdsregistry-api497-applicationxml-single-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#497 application/xml multi-product result does not contain blobs](#nasa-pdsregistry-api497-applicationxml-multi-product-result-does-not-contain-blobs)
  - [`GET`] [NASA-PDS/registry-api#516 Welcome page](#nasa-pdsregistry-api516-welcome-page)
  - [`GET`] [NASA-PDS/registry-api#439 I get application/json results from my browser](#nasa-pdsregistry-api439-i-get-applicationjson-results-from-my-browser)
  - [`GET`] [NASA-PDS/registry-api#440 get pds4+xml results on multiple products responses](#nasa-pdsregistry-api440-get-pds4xml-results-on-multiple-products-responses)
  - [`GET`] [NASA-PDS/registry-api#440 get pds4+xml results on single product responses](#nasa-pdsregistry-api440-get-pds4xml-results-on-single-product-responses)
  - [`GET`] [NASA-PDS/registry-api#450 get pds4+json results on multiple products responses](#nasa-pdsregistry-api450-get-pds4json-results-on-multiple-products-responses)
  - [`GET`] [NASA-PDS/registry-api#440 get pds4+json results on single product responses](#nasa-pdsregistry-api440-get-pds4json-results-on-single-product-responses)
  - [`GET`] [NASA-PDS/registry-api#459 return requested fields only text/csv](#nasa-pdsregistry-api459-return-requested-fields-only-textcsv)
  - [`GET`] [NASA-PDS/registry-api#459 return requested fields only application/kvp+json](#nasa-pdsregistry-api459-return-requested-fields-only-applicationkvpjson)
  - [`GET`] [NASA-PDS/registry-api#459 return requested fields only application/json](#nasa-pdsregistry-api459-return-requested-fields-only-applicationjson)
  - [`GET`] [NASA-PDS/registry-api#283 facets on terms](#nasa-pdsregistry-api283-facets-on-terms)
  - [`GET`] [NASA-PDS/registry-api#406 search on existent field](#nasa-pdsregistry-api406-search-on-existent-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on existent wildcard field](#nasa-pdsregistry-api406-search-on-existent-wildcard-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on non-existent field](#nasa-pdsregistry-api406-search-on-non-existent-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on non-existent wildcard field](#nasa-pdsregistry-api406-search-on-non-existent-wildcard-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on NOT non-existent field](#nasa-pdsregistry-api406-search-on-not-non-existent-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on NOT non-existent wildcard field](#nasa-pdsregistry-api406-search-on-not-non-existent-wildcard-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on NOT existent field](#nasa-pdsregistry-api406-search-on-not-existent-field)
  - [`GET`] [NASA-PDS/registry-api#406 search on NOT existent wildcard field](#nasa-pdsregistry-api406-search-on-not-existent-wildcard-field)
- [other tickets](#other-tickets)
  - [`GET`] [NASA-PDS/registry-api#277 /properties endpoint](#nasa-pdsregistry-api277-properties-endpoint)
  - [`GET`] [NASA-PDS/registry-api#326 list product classes](#nasa-pdsregistry-api326-list-product-classes)
  - [`GET`] [NASA-PDS/registry-api#375 csv response, use | as inner list separator](#nasa-pdsregistry-api375-csv-response-use-as-inner-list-separator)
  - [`GET`] [NASA-PDS/registry-api#296 API crashes with JVM memory error on data sets with very large labels (>1MB)](#nasa-pdsregistry-api296-api-crashes-with-jvm-memory-error-on-data-sets-with-very-large-labels-1mb)
  - [`GET`] [NASA-PDS/registry-api#356 Accept:* response not defaulting to valid application/json](#nasa-pdsregistry-api356-accept-response-not-defaulting-to-valid-applicationjson)
  - [`GET`] [NASA-PDS/registry-api#262 the request url in the error message does not make sense](#nasa-pdsregistry-api262-the-request-url-in-the-error-message-does-not-make-sense)
  - [`GET`] [NASA-PDS/registry-api#341 members of a bundle does not work on new test dataset](#nasa-pdsregistry-api341-members-of-a-bundle-does-not-work-on-new-test-dataset)
  - [`GET`] [NASA-PDS/registry-api#355 api does not return information that OpenSearch says is public](#nasa-pdsregistry-api355-api-does-not-return-information-that-opensearch-says-is-public)
  - [`GET`] [NASA-PDS/registry-api#343 API falsely reports 10000 hits for hits>10000](#nasa-pdsregistry-api343-api-falsely-reports-10000-hits-for-hits10000)
  - [`GET`] [NASA-PDS/registry-api/#638 a query without Accept header returns Json](#nasa-pdsregistry-api638-a-query-without-accept-header-returns-json)
- [opensearch requests](#opensearch-requests)
  - [`GET`] [legacy_registry](#legacy_registry)
- [pds web](#pds-web)
  - [`GET`] [class eq and lid like](#class-eq-and-lid-like)
  - [`GET`] [count having host and target](#count-having-host-and-target)
- [security](#security)
  - [`GET`] [unknown query parameters](#unknown-query-parameters)
  - [`GET`] [web cache poisoning](#web-cache-poisoning)

---

## cookbook examples

### `GET` Latest lidvid for a given lid (no suffix))

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice`

**Tests:**

- Status code is 200 ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))
- Response takes less than 1s ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))
- id is the latest lidvid available ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))

---

### `GET` Latest lidvid for a given lid (latest suffix)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/latest`

**Tests:**

- Status code is 200 ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))
- Response takes less than 1s ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))
- id is the latest lidvid available ([C2488906](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488906))

---

### `GET` All lidvid for a given lid (all suffix)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/all`

**Tests:**

- Status code is 200 ([C2488907](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488907))
- Response takes less than 1s ([C2488907](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488907))
- 3 products are found ([C2488907](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488907))

---

### `GET` Search by processing level

**URL:** `{{baseUrl}}/products?q=(pds:Primary_Result_Summary.pds:processing_level eq "Derived")&limit=10`

**Tests:**

- Status code is 200 ([C2488908](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488908))
- Response takes less than 1s ([C2488908](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488908))
- Number of results is 10 ([C2488908](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488908))
- processing level is derived ([C2488908](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488908))

---

### `GET` Search by target

**URL:** `{{baseUrl}}/products?q=(ref_lid_target eq "urn:nasa:pds:context:target:planet.mars")&limit=10`

**Tests:**

- Status code is 200 ([C2488910](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488910))
- Response takes less than 1s ([C2488910](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488910))
- Number of results is 10 ([C2488910](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488910))
- target is mars ([C2488910](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488910))

---

### `GET` Search by reference

**URL:** `{{baseUrl}}/products?q=((pds:Internal_Reference.pds:lid_reference eq "urn:nasa:pds:context:investigation:mission.mars2020") or (pds:Internal_Reference.pds:lid_reference like "urn:nasa:pds:context:investigation:mission.mars2020::*"))&limit=200`

**Tests:**

- Status code is 200 ([C2488911](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488911))
- Response takes less than 1s ([C2488911](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488911))
- 3 products are found ([C2488911](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488911))

---

### `GET` search for collection of an observtional product, kvp response

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad:data_calibrated:hp3_rad_cal_00014_20181211_073042::1.0/member-of?fields=pds:Citation_Information.pds:doi`

**Accept:** `application/kvp+json`

**Tests:**

- Status code is 200 ([C2488912](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488912))
- Response takes less than 1s ([C2488912](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488912))
- Has pds:Citation_Information.pds:doi ([C2488912](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488912))
- Collection DOI is [10.17189/1517568] ([C2488912](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488912))

---

### `GET` Search for a product knowing its DOI

**URL:** `{{baseUrl}}/products?q=(pds:Citation_Information.pds:doi eq "10.17189/1517568")`

**Tests:**

- Status code is 200 ([C2552353](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2552353))
- Response takes less than 1s ([C2552353](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2552353))
- number of results is 2 ([C2552353](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2552353))
- product DOI is [10.17189/1517568] ([C2488912](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488912))

---

## requirements

### `GET` NASA-PDS/registry-api#494 querystring supports EQ

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(product_class eq "Product_Bundle")`

---

### `GET` NASA-PDS/registry-api#494 querystring supports NE

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(product_class NE "Product_Bundle")`

---

### `GET` NASA-PDS/registry-api#494 querystring supports GT

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(pds:Time_Coordinates.pds:start_date_time GT "2020-07-30T12:51:34Z")`

---

### `GET` NASA-PDS/registry-api#494 querystring supports LT

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(pds:Time_Coordinates.pds:start_date_time LT "2020-07-30T12:51:34Z")`

---

### `GET` NASA-PDS/registry-api#494 querystring supports GE

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(pds:Time_Coordinates.pds:start_date_time GE "2020-07-30T12:51:34Z")`

---

### `GET` NASA-PDS/registry-api#494 querystring supports LE

**GitHub:** [NASA-PDS/registry-api#494](https://github.com/NASA-PDS/registry-api/issues/494)

**URL:** `{{baseUrl}}/products?q=(pds:Time_Coordinates.pds:start_date_time LE "2020-07-30T12:51:34Z")`

---

### `GET` NASA-PDS/registry-api#495 querystring supports AND

**GitHub:** [NASA-PDS/registry-api#495](https://github.com/NASA-PDS/registry-api/issues/495)

**URL:** `{{baseUrl}}/products?q=((product_class EQ "Product_Bundle") AND (lid EQ "urn:nasa:pds:mars2020.spice"))`

**Tests:**

- Status code is 200 ([C4440388](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440388))
- Number of results is 1 ([C4440388](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440388))
- Returned hits contain correct values ([C4440388](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440388))

---

### `GET` NASA-PDS/registry-api#495 querystring supports OR

**GitHub:** [NASA-PDS/registry-api#495](https://github.com/NASA-PDS/registry-api/issues/495)

**URL:** `{{baseUrl}}/products?q=((product_class EQ "Product_Bundle") AND ((lid EQ "urn:nasa:pds:mars2020.spice") OR (lid EQ "urn:nasa:pds:insight_rad")))`

**Tests:**

- Status code is 200 ([C4440389](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440389))
- Number of results is 2 ([C4440389](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440389))
- Returned hits contain correct values ([C4440389](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440389))

---

### `GET` NASA-PDS/registry-api#495 querystring supports NOT

**GitHub:** [NASA-PDS/registry-api#495](https://github.com/NASA-PDS/registry-api/issues/495)

**URL:** `{{baseUrl}}/products?q=((product_class EQ "Product_Bundle") AND NOT (lid EQ "urn:nasa:pds:mars2020.spice"))`

**Tests:**

- Status code is 200 ([C4440390](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440390))
- Number of results is 1 ([C4440390](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440390))
- Returned hits contain correct values ([C4440390](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440390))

---

### `GET` NASA-PDS/registry-api#493 querystring supports NOT on other endpoint

**GitHub:** [NASA-PDS/registry-api#493](https://github.com/NASA-PDS/registry-api/issues/493)

**URL:** `{{baseUrl}}/classes/bundle?q=((product_class EQ "Product_Bundle") AND NOT (lid EQ "urn:nasa:pds:mars2020.spice"))`

**Tests:**

- Status code is 200 ([C4443889](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4443889))
- Number of results is 1 ([C4443889](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4443889))
- Returned hits contain correct values ([C4443889](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4443889))

---

### `GET` NASA-PDS/registry-api#495 querystring supports lowercase operators

**GitHub:** [NASA-PDS/registry-api#495](https://github.com/NASA-PDS/registry-api/issues/495)

**URL:** `{{baseUrl}}/products?q=((product_class eq "Product_Bundle") and not (lid eq "urn:nasa:pds:mars2020.spice"))`

**Tests:**

- Status code is 200 ([C4440391](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440391))
- Number of results is 1 ([C4440391](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440391))
- Returned hits contain correct values ([C4440391](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4440391))

---

### `GET` NASA-PDS/pds-api#72 search by a temporal range as an ISO-8601 time interval

**GitHub:** [NASA-PDS/pds-api#72](https://github.com/NASA-PDS/pds-api/issues/72)

**URL:** `{{baseUrl}}/products?q=((pds:Time_Coordinates.pds:start_date_time gt "2021-03-03T01:36:00.000Z") and (pds:Time_Coordinates.pds:start_date_time lt "2021-03-03T02:36:46.542Z"))`

**Tests:**

- Status code is 200 ([C2488851](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488851))
- Number of results is 1 ([C2488851](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488851))
- time found in range ([C2488851](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488851))

---

### `GET` NASA-PDS/pds-api#99 free text search

**GitHub:** [NASA-PDS/pds-api#99](https://github.com/NASA-PDS/pds-api/issues/99)

**URL:** `{{baseUrl}}/products?keywords=Perseverance`

**Tests:**

- Status code is 200 ([C2488859](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488859))
- Response takes less than 1s ([C2488859](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488859))
- Number of results is 2 ([C2488859](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488859))
- title contains Perseverance ([C2488859](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488859))

---

### `GET` NASA-PDS/registry-api#80 select fields in response for lid/lidvid resolution

**GitHub:** [NASA-PDS/registry-api#80](https://github.com/NASA-PDS/registry-api/issues/80)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice::1.0?fields=lid,pds:File.pds:file_size`

**Accept:** `application/kvp+json`

**Tests:**

- Response takes less than 1s ([C2488846](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488846))
- Status code is 200 ([C2488846](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488846))
- Has lid ([C2488846](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488846))
- Has pds:File.pds:file_size ([C2488846](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488846))
- Has not ref_lid_instrument ([C2488846](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488846))

---

### `GET` NASA-PDS/registry#153 all properties are searchable

**GitHub:** [NASA-PDS/registry#153](https://github.com/NASA-PDS/registry/issues/153)

**URL:** `{{baseUrl}}/products?q=(ops:Label_File_Info.ops:md5_checksum eq "5c955dae449823ffc9e3e1eba1c474de")`

**Tests:**

- Status code is 200 ([C2488821](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488821))
- Number of results is 1 ([C2488821](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488821))
- checksum value is 5c955dae449823ffc9e3e1eba1c474de ([C2488821](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488821))

---

### `GET` NASA-PDS/registry-api#349 Request for json+pds4 response fails in production

**GitHub:** [NASA-PDS/registry-api#349](https://github.com/NASA-PDS/registry-api/issues/349)

**URL:** `{{baseUrl}}/products`

**Accept:** `application/vnd.nasa.pds.pds4+json`

**Tests:**

- Status code is 200

---

### `GET` NASA-PDS/registry-api#336 As a PDS operator, I want to know the health of the registry API service

**GitHub:** [NASA-PDS/registry-api#336](https://github.com/NASA-PDS/registry-api/issues/336)

**URL:** `{{baseUrl}}/health`

**Tests:**

- Status code is 200

---

### `GET` NASA-PDS/registry-api/352 pagination step 1

**URL:** `{{baseUrl}}/products?sort=ops:Harvest_Info.ops:harvest_date_time&limit=2`

---

### `GET` NASA-PDS/registry-api/352 pagination step 2

**URL:** `{{baseUrl}}/products?sort=ops:Harvest_Info.ops:harvest_date_time&limit=2&search-after=2024-01-23T22:53:30.402453Z`

---

### `GET` NASA-PDS/registry-api/352 members pagination step 1

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad:data_calibrated::7.0/members?sort=ops:Harvest_Info.ops:harvest_date_time&limit=2`

---

### `GET` NASA-PDS/registry-api/352 members pagination step 2

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad:data_calibrated::7.0/members?sort=ops:Harvest_Info.ops:harvest_date_time&limit=2&search-after=2024-01-23T22:53:30.402453Z`

---

### `GET` NASA-PDS/registry-api#434 get product from lidvid

**GitHub:** [NASA-PDS/registry-api#434](https://github.com/NASA-PDS/registry-api/issues/434)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020::3.0`

**Accept:** `application/kvp+json`

**Tests:**

- Status code is 200 ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))
- Response takes less than 1s ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))

---

### `GET` NASA-PDS/registry-api#434 get product from lidvid not supported Accept

**GitHub:** [NASA-PDS/registry-api#434](https://github.com/NASA-PDS/registry-api/issues/434)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020::3.0`

**Accept:** `application/not+supported`

**Tests:**

- Status code is 406 ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))
- Response takes less than 1s ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))

---

### `GET` NASA-PDS/registry-api#434 get product from lidvid missing

**GitHub:** [NASA-PDS/registry-api#434](https://github.com/NASA-PDS/registry-api/issues/434)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020::3.0`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))
- Response takes less than 1s ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))
- Description match the requested lidvid ([C4326843](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4326843))

---

### `GET` NASA-PDS/registry-api#435 get latest product from lid

**GitHub:** [NASA-PDS/registry-api#435](https://github.com/NASA-PDS/registry-api/issues/435)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))
- Response takes less than 1s ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))
- Description match the requested lidvid ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))

---

### `GET` NASA-PDS/registry-api#435 get latest product from lid with explicit latest

**GitHub:** [NASA-PDS/registry-api#435](https://github.com/NASA-PDS/registry-api/issues/435)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/latest`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))
- Response takes less than 1s ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))
- Description match the requested lidvid ([C4328804](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4328804))

---

### `GET` NASA-PDS/registry-api#436 get all product for a given lid

**GitHub:** [NASA-PDS/registry-api#436](https://github.com/NASA-PDS/registry-api/issues/436)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/all`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Description match the requested lid ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Multiple products are returned ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 1

**GitHub:** [NASA-PDS/registry-api#436](https://github.com/NASA-PDS/registry-api/issues/436)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/all?limit=2&sort=ops:Harvest_Info.ops:harvest_date_time`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Description match the requested lid ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Page 1 returns 2 results ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 2

**GitHub:** [NASA-PDS/registry-api#436](https://github.com/NASA-PDS/registry-api/issues/436)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/all?limit=2&sort=vid&search-after=2.0`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Description match the requested lid ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- only 1 product is returned in last page ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#436 get all product for a given lid with pagination, page 2 missing sort

**GitHub:** [NASA-PDS/registry-api#436](https://github.com/NASA-PDS/registry-api/issues/436)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/all?limit=2&search-after=2024-04-30T19:15:08.324465Z`

**Accept:** `application/json`

**Tests:**

- Status code is 400 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#469 q param simple criteria

**GitHub:** [NASA-PDS/registry-api#469](https://github.com/NASA-PDS/registry-api/issues/469)

**URL:** `{{baseUrl}}/products`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api/issues/66 invalid q string

**URL:** `{{baseUrl}}/products?q=ops:Data_File_Info.ops:file_size gte 138172`

**Accept:** `application/json`

**Tests:**

- Status code is 400 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#457 q param like operator with wildcard

**GitHub:** [NASA-PDS/registry-api#457](https://github.com/NASA-PDS/registry-api/issues/457)

**URL:** `{{baseUrl}}/products?q=lid  like "urn:nasa:pds:insight_*"`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#469 q param criteria combination

**GitHub:** [NASA-PDS/registry-api#469](https://github.com/NASA-PDS/registry-api/issues/469)

**URL:** `{{baseUrl}}/products?limit=2&sort=ops:Harvest_Info.ops:harvest_date_time&search-after=2024-04-30T19:15:08.324465Z&q=( ( ops:Label_File_Info.ops:file_size ge 6805 and lid eq "urn:nasa:pds:insight_rad" ) or  ops:Label_File_Info.ops:file_ref eq   "http://localhost:81/archive/custom-datasets/naif3/bundle_mars2020_spice_v001.xml")`

**Accept:** `application/json`

**Tests:**

- Status code is 200 ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))
- Response takes less than 1s ([C4332661](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4332661))

---

### `GET` NASA-PDS/registry-api#223 products/{id}/members

**GitHub:** [NASA-PDS/registry-api#223](https://github.com/NASA-PDS/registry-api/issues/223)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/members?q=pds:Collection.pds:collection_type eq "SPICE Kernel"`

---

### `GET` NASA-PDS/registry-api#484 products/{id}/members default to latest-only

**GitHub:** [NASA-PDS/registry-api#484](https://github.com/NASA-PDS/registry-api/issues/484)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/members`

---

### `GET` NASA-PDS/registry-api#453 products/{id}/members/members

**GitHub:** [NASA-PDS/registry-api#453](https://github.com/NASA-PDS/registry-api/issues/453)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/members/members?q=pds:Time_Coordinates.pds:start_date_time eq "2020-07-30T12:51:34Z"`

---

### `GET` NASA-PDS/registry-api#485 products/{id}/members/members default to latest-only

**GitHub:** [NASA-PDS/registry-api#485](https://github.com/NASA-PDS/registry-api/issues/485)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/members/members`

---

### `GET` NASA-PDS/registry-api#451/452 products/{id}/member-of

**GitHub:** [NASA-PDS/registry-api#451](https://github.com/NASA-PDS/registry-api/issues/451)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/member-of?q=pds:Time_Coordinates.pds:start_date_time eq "2020-07-30T12:51:34Z"`

---

### `GET` NASA-PDS/registry-api#451/486 products/{id}/member-of default to latest-only

**GitHub:** [NASA-PDS/registry-api#451](https://github.com/NASA-PDS/registry-api/issues/451)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/member-of`

---

### `GET` NASA-PDS/registry-api#454 products/{id}/member-of/member-of

**GitHub:** [NASA-PDS/registry-api#454](https://github.com/NASA-PDS/registry-api/issues/454)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/member-of/member-of?q=pds:Time_Coordinates.pds:start_date_time eq "2020-07-30T12:51:34Z"`

**Tests:**

- Status code is 200 ([C4438466](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438466))
- Correct hits returned ([C4438466](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438466))
- Correct data returned ([C4438466](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438466))
- Correct data returned according to q param ([C4443890](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4443890))

---

### `GET` NASA-PDS/registry-api#487 products/{id}/member-of/member-of default to latest-only

**GitHub:** [NASA-PDS/registry-api#487](https://github.com/NASA-PDS/registry-api/issues/487)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice:spice_kernels:mk_m2020/member-of/member-of`

**Tests:**

- Status code is 200 ([C4438483](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438483))
- Correct hits returned ([C4438483](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438483))
- Correct data returned ([C4438483](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438483))

---

### `GET` NASA-PDS/registry-api#497 application/json multi product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products?limit=1`

**Accept:** `application/json`

**Tests:**

- json blob is not in the JSON summary response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the JSON summary response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- json blob is not in the JSON data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the JSON data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))

---

### `GET` NASA-PDS/registry-api#497 application/json single product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1`

**Accept:** `application/json`

**Tests:**

- json blob is not in the data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))

---

### `GET` NASA-PDS/registry-api#497 application/kvp+json multi-product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products?limit=1`

**Accept:** `application/kvp+json`

**Tests:**

- json blob is not in the KVP summary response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the KVP summary response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- json blob is not in the KVP data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the KVP data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))

---

### `GET` NASA-PDS/registry-api#497 application/kvp+json single product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1`

**Accept:** `application/kvp+json`

**Tests:**

- json blob is not in the KVP data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))
- xml blob is not in the KVP data response ([C4438480](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4438480))

---

### `GET` NASA-PDS/registry-api#497 application/xml single product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1`

**Accept:** `application/xml`

---

### `GET` NASA-PDS/registry-api#497 application/xml multi-product result does not contain blobs

**GitHub:** [NASA-PDS/registry-api#497](https://github.com/NASA-PDS/registry-api/issues/497)

**URL:** `{{baseUrl}}/products?limit=1`

**Accept:** `application/xml`

---

### `GET` NASA-PDS/registry-api#516 Welcome page

**GitHub:** [NASA-PDS/registry-api#516](https://github.com/NASA-PDS/registry-api/issues/516)

**URL:** `{{baseUrl}}`

**Accept:** `text/html`

**Tests:**

- Welcome page, base URL returns documentation ([C4439829](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/4439829))

---

### `GET` NASA-PDS/registry-api#439 I get application/json results from my browser

**GitHub:** [NASA-PDS/registry-api#439](https://github.com/NASA-PDS/registry-api/issues/439)

**URL:** `{{baseUrl}}/products`

**Accept:** `text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7`

**Tests:**

- Content-Type is application/json

---

### `GET` NASA-PDS/registry-api#440 get pds4+xml results on multiple products responses

**GitHub:** [NASA-PDS/registry-api#440](https://github.com/NASA-PDS/registry-api/issues/440)

**URL:** `{{baseUrl}}/products?limit=2`

**Accept:** `application/vnd.nasa.pds.pds4+xml`

**Tests:**

- Content-Type is text/xml

---

### `GET` NASA-PDS/registry-api#440 get pds4+xml results on single product responses

**GitHub:** [NASA-PDS/registry-api#440](https://github.com/NASA-PDS/registry-api/issues/440)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad:data_calibrated:hp3_rad_cal_00390_20200101_120222::1.0`

**Accept:** `application/vnd.nasa.pds.pds4+xml`

**Tests:**

- Content-Type is text/xml

---

### `GET` NASA-PDS/registry-api#450 get pds4+json results on multiple products responses

**GitHub:** [NASA-PDS/registry-api#450](https://github.com/NASA-PDS/registry-api/issues/450)

**URL:** `{{baseUrl}}/products?limit=2`

**Accept:** `application/vnd.nasa.pds.pds4+json`

**Tests:**

- Content-Type is application/json

---

### `GET` NASA-PDS/registry-api#440 get pds4+json results on single product responses

**GitHub:** [NASA-PDS/registry-api#440](https://github.com/NASA-PDS/registry-api/issues/440)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad:data_calibrated:hp3_rad_cal_00390_20200101_120222::1.0`

**Accept:** `application/vnd.nasa.pds.pds4+json`

**Tests:**

- Content-Type is application/json

---

### `GET` NASA-PDS/registry-api#459 return requested fields only text/csv

**GitHub:** [NASA-PDS/registry-api#459](https://github.com/NASA-PDS/registry-api/issues/459)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1?fields=lid`

**Accept:** `text/csv`

**Tests:**

- ${testrailId} Only lid is in the reponse

---

### `GET` NASA-PDS/registry-api#459 return requested fields only application/kvp+json

**GitHub:** [NASA-PDS/registry-api#459](https://github.com/NASA-PDS/registry-api/issues/459)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1?fields=lid`

**Accept:** `application/kvp+json`

**Tests:**

- ${testrailId} Only lid is in the reponse

---

### `GET` NASA-PDS/registry-api#459 return requested fields only application/json

**GitHub:** [NASA-PDS/registry-api#459](https://github.com/NASA-PDS/registry-api/issues/459)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:insight_rad::2.1?fields=lid`

**Accept:** `application/json`

**Tests:**

- ${testrailId} Only lid is in the reponse

---

### `GET` NASA-PDS/registry-api#283 facets on terms

**GitHub:** [NASA-PDS/registry-api#283](https://github.com/NASA-PDS/registry-api/issues/283)

**URL:** `{{baseUrl}}/products?facet-fields=product_class,vid&facet-limit=20&limit=0`

---

### `GET` NASA-PDS/registry-api#406 search on existent field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=(pds:Identification_Area.pds:logical_identifier exists)`

**Tests:**

- Status code is 200
- Response body contains summary with hits count
- Data array is present and not empty

---

### `GET` NASA-PDS/registry-api#406 search on existent wildcard field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=(.*logical_identifier exists)`

**Tests:**

- Status code is 200
- Response body contains summary with hits count
- Data array is present and not empty

---

### `GET` NASA-PDS/registry-api#406 search on non-existent field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=(pds:Identification_Area.pds:illogical_identifier exists)`

**Tests:**

- Status code is 200
- Response body is valid JSON

---

### `GET` NASA-PDS/registry-api#406 search on non-existent wildcard field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=(".*illogical_identifier" exists)`

**Tests:**

- Status code is 400

---

### `GET` NASA-PDS/registry-api#406 search on NOT non-existent field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=not (pds:Identification_Area.pds:illogical_identifier exists)`

**Tests:**

- Status code is 200
- Response has summary object with hits and properties
- Response has data array and it is not empty
- summary.hits is greater than 0

---

### `GET` NASA-PDS/registry-api#406 search on NOT non-existent wildcard field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=not (".*illogical_identifier" exists)`

**Tests:**

- Status code is 400

---

### `GET` NASA-PDS/registry-api#406 search on NOT existent field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=not (pds:Identification_Area.pds:logical_identifier exists)`

**Tests:**

- Status code is 200
- Response body is valid JSON object
- summary.hits exists and is a number

---

### `GET` NASA-PDS/registry-api#406 search on NOT existent wildcard field

**GitHub:** [NASA-PDS/registry-api#406](https://github.com/NASA-PDS/registry-api/issues/406)

**URL:** `{{baseUrl}}/products?q=not (pds:Identification_Area.pds:logical_identifier exists)`

**Tests:**

- Status code is 200
- Response body is valid JSON object
- summary.hits exists and is a number

---

## other tickets

### `GET` NASA-PDS/registry-api#277 /properties endpoint

**GitHub:** [NASA-PDS/registry-api#277](https://github.com/NASA-PDS/registry-api/issues/277)

**URL:** `{{baseUrl}}/properties`

**Accept:** `application/kvp+json`

**Tests:**

- Status code is 200 ([C2488844](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488844))
- Response takes less than 100ms ([C2488844](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488844))
- Response contains same number of properties ([C2488844](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488844))
- Response property objects follow expected schema ([C2488844](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488844))

---

### `GET` NASA-PDS/registry-api#326 list product classes

**GitHub:** [NASA-PDS/registry-api#326](https://github.com/NASA-PDS/registry-api/issues/326)

**URL:** `{{baseUrl}}/classes`

**Accept:** `application/jso`

**Tests:**

- Status code is 200 ([C2488845](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488845))
- Returns correct values ([C2488845](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2488845))

---

### `GET` NASA-PDS/registry-api#375 csv response, use | as inner list separator

**GitHub:** [NASA-PDS/registry-api#375](https://github.com/NASA-PDS/registry-api/issues/375)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice::1.0?fields=lid,pds:File.pds:file_size`

**Accept:** `application/kvp+json`

**Tests:**

- Status code is 200 ([C2723037](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2723037))
- Response takes less than 100ms ([C2723037](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2723037))
- file size value doesn ([C2723037](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2723037))

---

### `GET` NASA-PDS/registry-api#296 API crashes with JVM memory error on data sets with very large labels (>1MB)

**GitHub:** [NASA-PDS/registry-api#296](https://github.com/NASA-PDS/registry-api/issues/296)

**URL:** `{{baseUrl}}/products?q=lidvid%20like%20%22urn:nasa:pds:mars2020_sherloc*%22`

**Tests:**

- Query

---

### `GET` NASA-PDS/registry-api#356 Accept:* response not defaulting to valid application/json

**GitHub:** [NASA-PDS/registry-api#356](https://github.com/NASA-PDS/registry-api/issues/356)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice::1.0`

**Tests:**

- Status code is 200
- Content-Type should be

---

### `GET` NASA-PDS/registry-api#262 the request url in the error message does not make sense

**GitHub:** [NASA-PDS/registry-api#262](https://github.com/NASA-PDS/registry-api/issues/262)

**URL:** `{{baseUrl}}/classes//collections?q=""`

**Tests:**

- Status code is 404

---

### `GET` NASA-PDS/registry-api#341 members of a bundle does not work on new test dataset

**GitHub:** [NASA-PDS/registry-api#341](https://github.com/NASA-PDS/registry-api/issues/341)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice::3.0/members`

**Tests:**

- Status code is 200

---

### `GET` NASA-PDS/registry-api#355 api does not return information that OpenSearch says is public

**GitHub:** [NASA-PDS/registry-api#355](https://github.com/NASA-PDS/registry-api/issues/355)

**URL:** `{{baseUrl}}/products/urn:nasa:pds:mars2020.spice/members`

**Tests:**

- Status code is 200

---

### `GET` NASA-PDS/registry-api#343 API falsely reports 10000 hits for hits>10000

**GitHub:** [NASA-PDS/registry-api#343](https://github.com/NASA-PDS/registry-api/issues/343)

**URL:** `{{baseUrl}}/products?limit=100&q=product_class%20eq%20"Product_Observational"`

**Tests:**

- Status code is 200
- Hits are less than 10,000

---

### `GET` NASA-PDS/registry-api/#638 a query without Accept header returns Json

**URL:** `{{baseUrl}}/products`

**Tests:**

- ${testrailId} Status code is 200
- ${testrailId} Content-Type is application/json

---

## opensearch requests

### `GET` legacy_registry

**URL:** `{{opensearchUrl}}/en-legacy-registry/_search`

**Tests:**

- legacy_registry index exists ([C2723010](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2723010))
- equal 50 synchronized products, dev mode, one page ([C2723010](https://cae-testrail.jpl.nasa.gov/testrail/index.php?/cases/view/2723010))

---

## pds web

### `GET` class eq and lid like

**URL:** `{{baseUrl}}/products?q=(product_class eq "Product_Collection" and  lid  like "urn:nasa:pds:insight_*")&limit=9999&fields=lid`

**Accept:** `application/json`

---

### `GET` count having host and target

**URL:** `{{baseUrl}}/products?q=(pds:Internal_Reference.pds:lid_reference eq "urn:nasa:pds:context:instrument_host:spacecraft.insight" and ref_lid_target eq "urn:nasa:pds:context:target:planet.mars")&limit=0&fields=lid`

**Accept:** `application/json`

---

## security

### `GET` unknown query parameters

**URL:** `{{baseUrl}}/products?q=(pds:Primary_Result_Summary.pds:processing_level eq "Derived")&limit=10&malicious=anything`

**Tests:**

- Status code is 400

---

### `GET` web cache poisoning

**URL:** `{{baseUrl}}/products?limit=3`

**Tests:**

- Status code is 400

---
