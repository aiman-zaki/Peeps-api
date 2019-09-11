pipeline {
    agent any
    stages {
        stage ('Checkout') {
            steps{
                checkout scm
            }
        }
        stage ('docker build') {
            script {
                steps {
                    def customImage docker.build('peeps:latest','-f deployment/nginx/Dockerfile')
                }
            }
        }
        
    }
}