node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        sh '''#!/bin/bash
            eval $(cat .env | sed 's/^/export /')
            docker build -t peeps:`echo $APP_VERSION` -f deployment/nginx/Dockerfile .
        '''

    }
    stage('docker update'){
        sh '''#!/bin/bash
            #docker rm -f peeps
            #docker-compose stop
            #eval $(cat .env | sed 's/^/export /')
            #docker stack deploy -c docker-compose.yml peeps
        '''
    }

}
