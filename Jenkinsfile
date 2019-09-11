node {
    stage('checkout'){
        checkout scm
    }
    stage('docker build'){
        def customImage = docker.build('peeps:latest','-f deployment/nginx/Dockerfile .')
    }
    stage('docker update'){
        sh '''#!/bin/bash
            docker rm -f peeps
            docker run --name peeps -i -p 8080:8080 --network="host" -t peeps:latest
        '''
    }

}