# Performance Optimizations Made:

Analyzing performance bottlenecks. Reviewing the code to identify and fix the FPS drops.


Identifying performance bottlenecks:
1. Creating full-screen surfaces for each connection line and trail segment (very expensive)
2. Inefficient auto-iteration timing using modulo
3. Unnecessary sqrt calculations in distance comparisons
4. Too many particle effects created simultaneously


## Performance Optimizations Made:

1. **Fixed expensive surface creation**: Instead of creating a full-screen surface for each connection line and trail segment (very expensive), now using a single shared surface for all lines and all trails.

2. **Optimized auto-iteration timing**: Replaced the inefficient `pygame.time.get_ticks() % 15 == 0` check with a proper timer-based approach using `last_iteration_time` and `iteration_delay`.

3. **Optimized distance calculations**: Added `distance_squared_to()` method and use squared distances for comparisons to avoid expensive `sqrt()` calls during cluster assignment.

4. **Limited particle effects**: Added a maximum of 10 particle effects per iteration step to prevent performance issues when many points change clusters simultaneously.

5. **Optimized glow drawing**: Improved the glow effect to use a single surface instead of multiple small ones.

6. **Optimized mouse interactions**: Use squared distances for centroid selection on right-click.

These changes should significantly improve FPS when pressing auto or space. 
The main issue was creating hundreds of full-screen surfaces every frame; now it's just two surfaces per frame (one for connections, one for trails).
