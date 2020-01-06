node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        def version = readFile('VERSION')        
        def customImage = docker.build('peeps:'+version,' -f deployment/nginx/Dockerfile .')

    }
    stage('docker update'){
        def version = readFile('VERSION')
        sh """#!/bin/bash
            docker rm -f peeps
            APP_VERSION = ${version} docker-compose up -d 
        """
    }

}