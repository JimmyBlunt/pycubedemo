# Copyright (C) John Leach <john@johnleach.co.uk>
# Released under the terms of the GNU General Public License version 3

import BaseHTTPServer
import cgi
import cubehelper
import random
import thread


class ControllerServer(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
<html>
    <head>
      <title>LED Invaders</title>
      <script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    </head>
    <body>
        <style>
        button { font-size: 30px; height: 30%; margin: 0; }
        button[name=forward], button[name=back] { width: 100% }
        button[name=left],button[name=fire],button[name=right] { width: 32% }
        button[name=fire] { background-color: #ffcccc; }
        </style>
        <script>
        $(function() {
        $("button").click(function() {
          $("button").attr("disabled", true);
          $.ajax({
            type: "POST",
            url: "/" + $(this).attr("name"),
            timeout: 3000,
            error: function(data) {
              $("button").attr("disabled", false);
            },
            success: function(data) {
              $("button").attr("disabled", false);
            }
          });
          return false;
        });
        });
        </script>
        <p><button type='submit' name='forward'>FORWARD</button></p>
        <p><button type='submit' name='left'>LEFT</button>
        <button type='submit' name='fire'>FIRE</button>
        <button type='submit' name='right'>RIGHT</button></p>
        <p><button type='submit' name='back'>BACK</button></p>
    </body>
</html>
        """)

    def do_POST(self):
        action = self.path
        if 'forward' in action:
            self.server.player.move_forward()
        if 'back' in action:
            self.server.player.move_back()
        if 'left' in action:
            self.server.player.move_left()
        if 'right' in action:
            self.server.player.move_right()
        if 'fire' in action:
            self.server.player.fire()

        self.send_response(200)
        self.end_headers()


class Actor(object):
    def __init__(self, game, *args):
        self.game = game
        self.cube = self.game.cube
        self.set_position()
        self.set_colour()
        self.init()

    def set_colour(self, c=None):
        if c is None:
            c = cubehelper.random_color()
        self.colour = c

    def set_position(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def move_x(self, delta):
        self.x += delta
        if self.x < 0:
            self.x = 0
        if self.x > self.cube.size - 1:
            self.x = self.cube.size - 1

    def move_y(self, delta):
        self.y += delta
        if self.y < 0:
            self.y = 0
        if self.y > self.cube.size - 1:
            self.y = self.cube.size - 1

    def move_z(self, delta):
        self.z += delta
        if self.z < 0:
            self.z = 0
        if self.z > self.cube.size - 1:
            self.z = self.cube.size - 1

    def centre_x(self):
        self.x = self.cube.size / 2

    def centre_y(self):
        self.y = self.cube.size / 2

    def centre_z(self):
        self.z = self.cube.size / 2

    def coords(self):
        return (self.x, self.y, self.z)

    def draw(self):
        self.cube.set_pixel(self.coords(), self.colour)

    def collides_with(self, other):
        return self.coords() == other.coords()

    def init(self):
        pass

    def tick(self):
        pass


class Player(Actor):
    def init(self):
        self.set_colour((0, 99, 0))
        self.centre_x()
        self.centre_y()
        self.z = 0

    def move_forward(self):
        self.move_y(1)

    def move_back(self):
        self.move_y(-1)

    def move_left(self):
        self.move_x(-1)

    def move_right(self):
        self.move_x(1)

    def fire(self):
        if len(self.game.bullets) < 3:
            bullet = Bullet(self.game)
            self.game.bullets.append(bullet)


class Bullet(Actor):
    def init(self):
        self.set_colour((255, 255, 255))
        self.z = 0
        self.x = self.game.player.x
        self.y = self.game.player.y

        self.ticker = 0
        self.alive = True

    def tick(self):
        self.ticker += 1

        for invader in self.game.invaders:
            if self.collides_with(invader):
                invader.kill()
                self.game.bullets.remove(self)
                return
            if self.z >= self.cube.size-1:
                self.game.bullets.remove(self)
                return

        if self.ticker % 2 == 1:
            self.move_z(1)
            self.alive = self.z < self.cube.size-1


class Invader(Actor):
    def init(self):
        self.set_colour((255, 00, 00))
        self.x = random.randint(0, self.cube.size-1)
        self.y = random.randint(0, self.cube.size-1)
        self.z = self.cube.size-1
        self.speed = 20
        self.ticker = 0
        self.state = 'alive'
        self.opacity = 1.0

    def kill(self):
        self.game.score += 1
        self.state = 'dying'
        self.game.invaders.append(Invader(self.game))

    def tick(self):
        self.ticker += 1
        if self.state is 'alive':
            if self.ticker % self.speed == self.speed-1:
                self.move_z(-1)
            if self.z == 0:
                self.state = 'landed'
        elif self.state is 'dying':
            self.opacity -= 0.1
            if self.ticker % (self.speed) == self.speed-1:
                self.move_z(-1)
            if self.opacity <= 0.0:
                self.state = 'dead'
        elif self.state is 'dead':
            self.game.invaders.remove(self)
        elif self.state is 'landed':
            self.game.score -= 1
            self.game.invaders.remove(self)
            self.game.invaders.append(Invader(self.game))

    def draw(self):
        c = cubehelper.mix_color((0, 0, 0), self.colour, self.opacity)
        self.cube.set_pixel(self.coords(), c)

    def collides_with(self, other):
        return (self.state is 'alive' or self.state is 'landed') and \
            self.coords() == other.coords()


class Game(object):

    def __init__(self, cube):
        self.cube = cube
        self.level = 10
        self.player = Player(self)
        self.invaders = [Invader(self)]
        self.bullets = []
        self.score = 0

    def tick(self):
        self.cube.clear()
        self.player.tick()
        self.player.draw()
        for invader in self.invaders:
            invader.tick()
            invader.draw()
        for bullet in self.bullets:
            bullet.tick()
            bullet.draw()

        for i in range(1, 10):
            if self.score >= i * 3 and len(self.invaders) <  i:
                self.invaders.append(Invader(self))


class Pattern(object):
    def init(self):
        self.double_buffer = True
        self.game = Game(self.cube)
        self.controller_server = BaseHTTPServer.HTTPServer(("0.0.0.0", 3010), ControllerServer)
        self.controller_server.player = self.game.player
        self.controller_thread = thread.start_new_thread(self.controller_server.serve_forever, ())
        return 0.1

    def tick(self):
        self.game.tick()