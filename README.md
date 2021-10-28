# 🪐 NASA PDS Registry repository

This repository contains the PDS registry application. It is the aggregation of the different PDS registry sub-components (harvest, api...) and some starter script.

## How this repository was done

This repository uses subtree to reference the sub-components repository:

    git remote add pds-registry-common https://github.com/NASA-PDS/pds-registry-common.git
    git remote add harvest https://github.com/NASA-PDS/harvest.git
    git remote add registry-manager https://github.com/NASA-PDS/pds-registry-mgr-elastic.git
    git remote add pds-api-javalib https://github.com/NASA-PDS/pds-api-javalib.git
    git remote add api-search-query-lexer https://github.com/NASA-PDS/api-search-query-lexer.git
    git remote add registry-api-service https://github.com/NASA-PDS/registry-api-service.git 
	

    git subtree add --prefix pds-registry-common https://github.com/NASA-PDS/pds-registry-common.git main --squash
    git subtree add --prefix harvest https://github.com/NASA-PDS/harvest.git main --squash
    git subtree add --prefix registry-manager https://github.com/NASA-PDS/pds-registry-mgr-elastic.git main --squash
    git subtree add --prefix pds-api-javalib https://github.com/NASA-PDS/pds-api-javalib.git main --squash
    git subtree add --prefix api-search-query-lexer https://github.com/NASA-PDS/api-search-query-lexer.git main --squash
    git subtree add --prefix registry-api-service https://github.com/NASA-PDS/registry-api-service.git main --squash

## 🏃 Getting Started With This Respository

Build the sources:

    mvn clean install

Init the application with some data and start the backend services (elasticsearch db):

    ./init.sh &

Start the API service

    cd registry-api-service
    mvn spring-boot:run


## Developer

Create a branch on a subtree

    git subtree split --prefix=registry-api-service -b new_branch


Commit messsage for your updates:

    git commit -a -m 'dffdg' (as usual)


Update the remote branch

    git subtree push --prefix=registry-api-service registry-api-service new_branch



## 📃 License

The project is licensed under the [Apache version 2](LICENSE.md) license. Or it isn't. Change this after consulting with your lawyers.
