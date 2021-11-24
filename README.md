# 🪐 NASA PDS Registry repository

This repository contains the PDS registry application. It is the aggregation of the different PDS registry sub-components (harvest, api...) and some starter script.

## Prerequisite

To contribute to this repository you will need git subrepo (https://github.com/ingydotnet/git-subrepo):

    git clone https://github.com/ingydotnet/git-subrepo ~/tools/git-subrepo                                           
    echo 'source ~/tools/git-subrepo/.rc' >> ~/.bashrc
    source ~/.bashrc



## How this repository was done

This repository uses subtree to reference the sub-components repository:

    git subrepo clone https://github.com/NASA-PDS/pds-registry-common.git pds-registry-common
    git subrepo clone https://github.com/NASA-PDS/harvest.git harvest
    git subrepo clone https://github.com/NASA-PDS/pds-registry-mgr-elastic.git registry-manager
    git subrepo clone https://github.com/NASA-PDS/pds-api-javalib.git pds-api-javalib
    git subrepo clone https://github.com/NASA-PDS/api-search-query-lexer.git api-search-query-lexer
    git subrepo clone https://github.com/NASA-PDS/registry-api-service.git registry-api-service


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
