node {
    stage('checkout'){
        checkout scm
    }
    stage('docer build'){
        def customImage = docker.build('peeps:latest','-f deployment/nginx/Dockerfile .')
    }

}