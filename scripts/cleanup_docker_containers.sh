#!/bin/bash

# Docker Container Cleanup Script
# Stops and removes old buildkit containers and cleans up unused resources

echo "🐳 Docker Container & Resource Cleanup"
echo "======================================"

# Get current time in seconds since epoch
current_time=$(date +%s)
four_hours_ago=$((current_time - 14400))  # 4 hours = 14400 seconds

echo "Current time: $(date)"
echo "Cleaning containers older than: $(date -d @$four_hours_ago 2>/dev/null || date -r $four_hours_ago 2>/dev/null)"

echo ""
echo "Step 1: 🔍 Identifying old buildkit containers..."

# List all buildkit containers with their ages
echo "Current buildkit containers:"
docker ps --filter "ancestor=moby/buildkit:buildx-stable-1" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.CreatedAt}}"

echo ""
echo "Step 2: 🛑 Stopping and removing old buildkit containers..."

# Get container IDs that are older than 4 hours
old_containers=$(docker ps --filter "ancestor=moby/buildkit:buildx-stable-1" --format "{{.ID}} {{.CreatedAt}}" | while read id created_at; do
    # Parse the created time and convert to epoch
    # Handle different date formats
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        container_time=$(date -j -f "%Y-%m-%d %H:%M:%S %z" "$created_at" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$created_at" +%s 2>/dev/null)
    else
        # Linux
        container_time=$(date -d "$created_at" +%s 2>/dev/null)
    fi
    
    if [ $? -eq 0 ] && [ "$container_time" -lt "$four_hours_ago" ]; then
        echo $id
    fi
done)

if [ -z "$old_containers" ]; then
    echo "✅ No buildkit containers older than 4 hours found"
else
    echo "🗑️  Removing old containers:"
    for container in $old_containers; do
        container_name=$(docker ps --filter "id=$container" --format "{{.Names}}")
        echo "  Stopping and removing: $container ($container_name)"
        docker stop $container >/dev/null 2>&1
        docker rm $container >/dev/null 2>&1
        echo "  ✅ Removed: $container"
    done
fi

echo ""
echo "Step 3: 🧹 General Docker cleanup..."

# Remove all stopped containers
echo "Removing all stopped containers..."
stopped_containers=$(docker ps -aq --filter "status=exited")
if [ ! -z "$stopped_containers" ]; then
    docker rm $stopped_containers >/dev/null 2>&1
    echo "✅ Removed stopped containers"
else
    echo "✅ No stopped containers to remove"
fi

# Remove dangling images
echo "Removing dangling images..."
dangling_images=$(docker images -f "dangling=true" -q)
if [ ! -z "$dangling_images" ]; then
    docker rmi $dangling_images >/dev/null 2>&1
    echo "✅ Removed dangling images"
else
    echo "✅ No dangling images to remove"
fi

# Clean up build cache
echo "Cleaning Docker build cache..."
docker builder prune -f >/dev/null 2>&1
echo "✅ Build cache cleaned"

# Remove unused networks
echo "Removing unused networks..."
docker network prune -f >/dev/null 2>&1
echo "✅ Unused networks removed"

# Remove unused volumes (be careful with this)
echo "Checking for unused volumes..."
unused_volumes=$(docker volume ls -qf dangling=true)
if [ ! -z "$unused_volumes" ]; then
    echo "⚠️  Found unused volumes (not removing automatically for safety):"
    docker volume ls -f dangling=true
    echo "💡 To remove manually: docker volume prune"
else
    echo "✅ No unused volumes found"
fi

echo ""
echo "Step 4: 📊 Current Docker status after cleanup..."

echo "Active containers:"
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Docker disk usage:"
docker system df

echo ""
echo "✅ Docker cleanup completed!"
echo ""
echo "💡 To prevent buildkit container accumulation:"
echo "   docker buildx prune --force"
echo "   docker builder prune --all --force"
