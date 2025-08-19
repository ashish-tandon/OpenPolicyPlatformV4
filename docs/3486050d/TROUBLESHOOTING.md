# 🔧 Troubleshooting Guide

Common issues and solutions for OpenPolicyPlatform V4 migration.

## GitHub Actions Issues

### "Repository not found" error
**Problem**: CI/CD workflow cannot find the orchestration repository
**Solution**: 
1. Verify the repository name in the workflow file
2. Check the ORCHESTRATION_TOKEN secret is set correctly
3. Ensure the token has access to all repositories

### Docker build fails
**Problem**: Docker image build fails in GitHub Actions
**Solution**:
1. Check Dockerfile syntax and paths
2. Verify base image exists and is accessible
3. Review build logs for specific error messages
4. Ensure all required files are included in the build context

### Permission denied when pushing to container registry
**Problem**: Cannot push Docker images to GitHub Container Registry
**Solution**:
1. Verify GitHub token has package write permissions
2. Check repository settings allow package access
3. Ensure workflow has correct permissions block

## Azure Deployment Issues

### "Resource group not found"
**Problem**: Azure deployment script cannot find resource group
**Solution**:
1. Verify you're authenticated with the correct Azure subscription
2. Check the resource group name matches the deployment script
3. Ensure you have contributor access to the subscription

### Container App fails to start
**Problem**: Azure Container App shows "Failed" status
**Solution**:
1. Check the container logs in Azure Portal
2. Verify the Docker image exists and is accessible
3. Review environment variables and secrets configuration
4. Check resource limits (CPU/memory)

### Database connection fails
**Problem**: Services cannot connect to PostgreSQL database
**Solution**:
1. Verify firewall rules allow Azure services
2. Check connection string format and credentials
3. Ensure the database is running and accessible
4. Review network security group settings

## Docker/Local Development Issues

### Services fail to start locally
**Problem**: Docker Compose services exit immediately
**Solution**:
1. Check Docker Compose logs: `docker-compose logs <service-name>`
2. Verify environment variables in .env files
3. Ensure all required images can be built/pulled
4. Check port conflicts with other running services

### Database connection refused
**Problem**: Services cannot connect to local PostgreSQL
**Solution**:
1. Verify PostgreSQL container is running: `docker-compose ps`
2. Check database credentials match environment variables
3. Ensure the database has been initialized properly
4. Review Docker network configuration

### Port already in use
**Problem**: Cannot start services due to port conflicts
**Solution**:
1. Stop conflicting services: `docker-compose down`
2. Change port mappings in docker-compose.yml
3. Kill processes using the ports: `lsof -ti:3000 | xargs kill`

## QNAP Container Station Issues

### Cannot connect to QNAP
**Problem**: SSH connection to QNAP fails
**Solution**:
1. Verify QNAP IP address and SSH port
2. Check SSH is enabled in QNAP settings
3. Verify network connectivity: `ping <qnap-ip>`
4. Ensure SSH key authentication is configured

### Container Station not accessible
**Problem**: Cannot access Container Station web interface
**Solution**:
1. Verify Container Station is installed on QNAP
2. Check Container Station service is running
3. Verify web interface port (usually 8080)
4. Review QNAP firewall settings

### Blue-green deployment fails
**Problem**: Traffic switching doesn't work correctly
**Solution**:
1. Check nginx configuration syntax
2. Verify container health checks are passing
3. Review container logs for startup issues
4. Ensure network connectivity between containers

## Service-Specific Issues

### Health checks failing
**Problem**: Service health endpoints return errors
**Solution**:
1. Verify health check endpoint exists and responds
2. Check service startup time vs health check timing
3. Review service logs for startup errors
4. Ensure dependencies (database, redis) are available

### Service discovery problems
**Problem**: Services cannot communicate with each other
**Solution**:
1. Verify service names match Docker Compose configuration
2. Check network configuration allows inter-service communication
3. Review firewall and security group settings
4. Test connectivity manually: `curl http://service-name:port/health`

### Memory/CPU issues
**Problem**: Services running out of resources
**Solution**:
1. Increase resource limits in docker-compose.yml
2. Review application memory usage patterns
3. Optimize application performance
4. Consider horizontal scaling

## Security Issues

### Secrets not accessible
**Problem**: Applications cannot access Azure Key Vault secrets
**Solution**:
1. Verify managed identity has Key Vault access
2. Check secret names match application configuration
3. Review Key Vault access policies
4. Ensure secrets exist in the correct Key Vault

### Authentication failures
**Problem**: Inter-service authentication fails
**Solution**:
1. Verify JWT tokens are correctly configured
2. Check shared secrets between services
3. Review token expiration settings
4. Ensure clock synchronization between services

## Performance Issues

### Slow response times
**Problem**: Services respond slowly to requests
**Solution**:
1. Review database query performance
2. Check network latency between services
3. Monitor resource utilization
4. Consider caching strategies

### High resource usage
**Problem**: Services consume too much CPU/memory
**Solution**:
1. Profile application performance
2. Review inefficient code patterns
3. Optimize database queries
4. Consider connection pooling

## Getting Help

If these solutions don't resolve your issue:

1. **Check logs systematically**:
   - GitHub Actions workflow logs
   - Azure Container App logs
   - Docker container logs
   - QNAP Container Station logs

2. **Verify configuration**:
   - Environment variables
   - Secret values
   - Network settings
   - Resource limits

3. **Test incrementally**:
   - Start with one service
   - Verify each component independently
   - Add complexity gradually

4. **Community resources**:
   - GitHub Issues in the repository
   - Azure documentation
   - Docker documentation
   - QNAP community forums

## Prevention Tips

- **Monitor continuously**: Set up comprehensive monitoring from day one
- **Test regularly**: Run automated tests in all environments
- **Document changes**: Keep deployment and configuration docs updated
- **Backup frequently**: Regular backups of databases and configurations
- **Review logs**: Regular log analysis to catch issues early

Remember: Microservices add complexity but also provide better isolation for debugging. When issues occur, they're usually isolated to specific services rather than affecting the entire system.
