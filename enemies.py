import pygame
import math
import game_tools


class Enemy:
    def __init__(self, position, health, money, speed, image_path, path=game_tools.house_path):
        self.position = position  # (x, y) tuple
        self.health = health
        self.money = money
        self.speed = speed
        self.path = path  # List of (x, y) points the enemy follows
        self.original_image = game_tools.load_image(image_path)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=position)
        self.img_death = pygame.image.load("assets/splatter.png")
        self.size = self.rect.size  # Width and height of the enemy
        self.current_target = 0  # Current target index in the path
        self.is_alive = True
        self.sfx_splat = pygame.mixer.Sound("assets/splat_sfx.mp3")

    def move(self):
        # Move towards the next point in the path
        if self.current_target < len(self.path):
            target_x, target_y = self.path[self.current_target]
            dx = target_x - self.position[0]
            dy = target_y - self.position[1]
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance == 0:  # Avoid division by zero
                return

            # Calculate normalized direction vector
            direction_x = dx / distance
            direction_y = dy / distance

            # Move enemy by speed in the direction of the target
            self.position = (
                self.position[0] + direction_x * self.speed,
                self.position[1] + direction_y * self.speed
            )
            self.rect.center = self.position

            # Rotate the enemy to face the target
            self.update_orientation(direction_x, direction_y)

            # Check if the enemy reached the target
            if distance <= self.speed:
                self.current_target += 1

        # If the enemy has reached the end of the path
        if self.current_target >= len(self.path):
            self.is_alive = False  # Mark as no longer active (escaped)
            game_tools.user_health -= self.health

    def update_orientation(self, direction_x, direction_y):
        """Rotate the image to face the movement direction."""
        # Calculate angle in radians and convert to degrees
        angle = math.degrees(math.atan2(-direction_y, direction_x))  # Flip y-axis for Pygame
        self.image = pygame.transform.rotate(self.original_image, angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def take_damage(self, *args):
        self.health -= args[0]
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money

    def render(self, screen):
        # Draw the enemy on the screen
        if self.is_alive:
            screen.blit(self.image, self.rect.topleft)
        if not self.is_alive:
            screen.blit(self.img_death, self.rect.topleft)
            # Optionally, draw the health bar
            # pygame.draw.rect(screen, (255, 0, 0), (*self.rect.topleft, self.size[0], 5))
            # pygame.draw.rect(
            #     screen,
            #     (0, 255, 0),
            #     (*self.rect.topleft, self.size[0] * (self.health / 100), 5)
            # )


class AntEnemy(Enemy):
    def __init__(self, position=(238, 500), health=1, money=5, speed=1, image_path="assets/ant_base.png"):
        super().__init__(position, health, money, speed, image_path)


class HornetEnemy(Enemy):
    def __init__(self, position=(238, 500), health=3, money=10, speed=2, image_path="assets/hornet_base.png"):
        super().__init__(position, health, money, speed, image_path)


class CentipedeEnemy:
    """
    A composite enemy consisting of:
      - Head (health=6)
      - 4 Link segments (each health=3)
      - Tail (health=3)
    Movement is fluid: each segment follows the one ahead with a smoothing delay.
    Damage is applied to the furthest (tail-first) alive segment until only the head remains.
    Speed is 1 initially, increases to 2 when 3 or fewer non-head segments remain,
    and becomes 3 when only the head is left.
    The images are flipped horizontally in rendering.
    """
    sfx_splat = game_tools.load_sound("assets/splat_sfx.mp3")
    img_death = game_tools.load_image("assets/splatter.png")

    class Segment:
        def __init__(self, role, health, image, position):
            self.role = role  # "head", "link", or "tail"
            self.health = health
            self.image = image
            self.position = position  # (x, y)
            self.angle = 0  # in degrees; 0 means "facing up"
            self.alive = True
            self.death_time = None  # Stores the time of death
            self.rect = self.image.get_rect(center=position)

        def update_rect(self):
            self.rect = self.image.get_rect(center=self.position)

    def __init__(self, position, path):
        """
        :param position: Starting position (tuple)
        :param path: List of points (tuples) for the centipede head to follow.
        """
        self.path = path
        self.current_target = 0  # Index in the path for head movement
        self.base_speed = 1      # Initial speed
        self.speed = self.base_speed

        # Load images
        head_img = game_tools.load_image("assets/centipede_head.png")
        link_img = game_tools.load_image("assets/centipede_link.png")
        tail_img = game_tools.load_image("assets/centipede_tail.png")

        # Calculate desired gap distances (so segments appear connected)
        # Gaps are computed based on half-heights of adjacent images.
        self.gap_distances = []
        gap_head_link = (head_img.get_height() / 4) + (link_img.get_height() / 4)
        self.gap_distances.append(gap_head_link)
        # For the gaps between the 4 links (using link height)
        for _ in range(5):
            gap_link_link = link_img.get_height() / 4
            self.gap_distances.append(gap_link_link)
        gap_link_tail = (link_img.get_height() / 4) + (tail_img.get_height() / 4)
        self.gap_distances.append(gap_link_tail)

        # Create segments. All segments start at the same initial position.
        self.segments = []
        # Head segment with health 6.
        self.segments.append(self.Segment("head", 6, head_img, position))
        # 6 link segments, each with health 2.
        for _ in range(6):
            self.segments.append(self.Segment("link", 2, link_img, position))
        # Tail segment with health 3.
        self.segments.append(self.Segment("tail", 3, tail_img, position))

    def update(self):
        """
        Update the centipede:
          - Move the head along its path.
          - Smoothly update each following segment so that it trails its predecessor.
          - Adjust the speed based on the number of non-head segments still alive.
          - Remove the centipede and subtract health if it reaches the end of the path.
        """
        global user_health  # Ensure this matches how health is tracked in your game

        # Determine how many non-head segments are still alive.
        non_head_alive = sum(1 for seg in self.segments[1:] if seg.alive)
        if non_head_alive >= 4:
            self.speed = 1
        elif non_head_alive > 0:
            self.speed = 2
        else:
            self.speed = 3

        # === Move the head along the path ===
        head = self.segments[0]
        if self.current_target < len(self.path):
            target_point = self.path[self.current_target]
            dx = target_point[0] - head.position[0]
            dy = target_point[1] - head.position[1]
            distance = math.hypot(dx, dy)
            if distance:
                dir_x = dx / distance
                dir_y = dy / distance
                move_dist = self.speed
                new_x = head.position[0] + dir_x * move_dist
                new_y = head.position[1] + dir_y * move_dist
                head.position = (new_x, new_y)
                head.angle = math.degrees(math.atan2(dir_x, -dir_y))
                head.update_rect()
                if distance <= move_dist:
                    self.current_target += 1
        else:
            # Centipede reaches the end of the path
            game_tools.user_health -= head.health  # Subtract health when the enemy escapes
            self.segments.clear()  # Remove all segments so it disappears
            return

        # === Smoothly update each following segment ===
        alpha = 0.2  # Smoothing factor
        for i in range(1, len(self.segments)):
            prev_seg = self.segments[i - 1]
            seg = self.segments[i]
            desired_gap = self.gap_distances[i - 1]
            vec_x = prev_seg.position[0] - seg.position[0]
            vec_y = prev_seg.position[1] - seg.position[1]
            dist = math.hypot(vec_x, vec_y)
            if dist:
                dir_x = vec_x / dist
                dir_y = vec_y / dist
                target_x = prev_seg.position[0] - desired_gap * dir_x
                target_y = prev_seg.position[1] - desired_gap * dir_y
                new_x = seg.position[0] + alpha * (target_x - seg.position[0])
                new_y = seg.position[1] + alpha * (target_y - seg.position[1])
                seg.position = (new_x, new_y)
                desired_angle = math.degrees(math.atan2(dir_x, -dir_y))
                seg.angle += alpha * ((desired_angle - seg.angle + 180) % 360 - 180)
                seg.update_rect()

    def move(self):
        """Alias move() to update() for compatibility with the game loop."""
        self.update()

    def take_damage(self, damage):
        global money
        """
        Apply damage to the centipede:
          - Damage is applied to the furthest (tail-first) alive segment among the links/tail.
          - Only if all non-head segments are destroyed is damage applied to the head.
        """
        for seg in reversed(self.segments[1:]):  # Prioritize tail & links first
            if seg.alive:
                seg.health -= damage
                if seg.health <= 0:
                    seg.alive = False
                    game_tools.money += 15
                    self.sfx_splat.play()
                    seg.death_time = pygame.time.get_ticks()  # Mark the time of death
                return  # Exit after applying damage.

        # If all non-head segments are destroyed, apply damage to the head.
        head = self.segments[0]
        head.health -= damage
        if head.health <= 0:
            head.alive = False
            money += 25
            self.sfx_splat.play()
            head.death_time = pygame.time.get_ticks()

    def render(self, screen: pygame.Surface):
        """
        Render each alive segment with its current rotation.
        Show the splatter effect for a brief time after death.
        """
        current_time = pygame.time.get_ticks()
        splatter_duration = 100  # Time in milliseconds to show the splatter (0.5 seconds)

        for seg in self.segments:
            if seg.alive:
                # Render living segments
                rotated_image = pygame.transform.rotate(seg.image, seg.angle)
                rotated_image = pygame.transform.flip(rotated_image, True, False)  # Flip horizontally
                rect = rotated_image.get_rect(center=seg.position)
                screen.blit(rotated_image, rect.topleft)
            elif seg.death_time and current_time - seg.death_time <= splatter_duration:
                # Render splatter effect for a limited time
                rotated_splatter = pygame.transform.rotate(self.img_death, seg.angle)
                rotated_splatter = pygame.transform.flip(rotated_splatter, True, False)
                rect = rotated_splatter.get_rect(center=seg.position)
                screen.blit(rotated_splatter, rect.topleft)

    @property
    def position(self):
        """
        Expose the centipede's effective position as the position of the furthest (tail-most)
        alive segment. This helps towers target the centipede's remaining body.
        """
        for seg in reversed(self.segments):
            if seg.alive:
                return seg.position
        return self.segments[0].position

    @property
    def is_alive(self):
        """
        The centipede is considered alive as long as its head is alive.
        If all segments are cleared (e.g., reached the end), return False.
        """
        return bool(self.segments) and self.segments[0].alive


class CentipedeBoss(Enemy):
    def __init__(self, index, position=(238, 500), health=5, money=15, speed=1, image_path="assets/centipede_head.png"):
        super().__init__(position, health, money, speed, image_path)
        self.index = index

    def update_orientation(self, direction_x, direction_y):
        if self.index == game_tools.enemies[0].index:
            self.image = game_tools.load_image("assets/centipede_head.png")
        super().update_orientation(direction_x, direction_y)

    def take_damage(self, damage):
        if self.index == game_tools.enemies[0].index:
            self.health -= damage
        if self.health <= 0:
            self.is_alive = False
            self.sfx_splat.play()
            game_tools.money += self.money
