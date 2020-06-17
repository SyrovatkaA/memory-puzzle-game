"""
Memory Puzzle Game
By Al Sweigart
"""

import sys
import random
import pygame
import pygame.locals

FPS = 30 # frames per second
WINDOWWIDTH = 640 # width of the whole window in px
WINDOWHEIGHT = 480 # height of the whole window in px
REVEALSPEED = 8
BOXSIZE = 40 # the size of each of the cards in px
GAPSIZE = 10 # the gap between cards in px
BOARDWIDTH = 10 # this number of cards per line
BOARDHEIGHT = 7 # this number of cards per column
assert (BOARDWIDTH * BOARDHEIGHT) % 2 == 0, \
    'Board needs to have an even number of boxes for pairs of matches' \
    # assert even number of cards (e.g. 70), otherway the game has no sense
XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * (BOXSIZE + GAPSIZE))) / 2) \
    # calculate margin between left/right border of the window and the nearest card
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * (BOXSIZE + GAPSIZE))) / 2) \
    # calculate margin between top/bottom border of the window and the nearest card

GRAY = (100, 100, 100)
NAVYBLUE = (60, 60, 100)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)

BGCOLOR = NAVYBLUE
LIGHTBGCOLOR = GRAY
BOXCOLOR = WHITE
HIGHLIGHTCOLOR = BLUE

DONUT = 'donut'
SQUARE = 'square'
DIAMOND = 'diamond'
LINES = 'lines'
OVAL = 'oval'

ALLCOLORS = (RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN)
ALLSHAPES = (DONUT, SQUARE, DIAMOND, LINES, OVAL)
assert len(ALLCOLORS) * len(ALLSHAPES) * 2 >= BOARDWIDTH * BOARDHEIGHT, \
    'Board is too big for the number of shapes/colors defined.' \
    # make sure that all combinations of shape and color can fit into the board \
    # (maybe more but not less)

def main():
    """The main part of the game code"""
    global FPSCLOCK, DISPLAYSURF
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

    mousex = 0
    mousey = 0
    pygame.display.set_caption('Memory Game')

    main_board = get_randomized_board()
    revealed_boxes = generate_revealed_boxes_data(False)

    first_selection = (-1, -1) # stores (x, y) of the first clicked card

    DISPLAYSURF.fill(BGCOLOR)
    start_game_animation(main_board)

    while True:
        mouse_clicked = False

        DISPLAYSURF.fill(BGCOLOR)
        draw_board(main_board, revealed_boxes)

        for event in pygame.event.get():
            if (event.type == pygame.locals.QUIT) \
                or (event.type == pygame.locals.KEYUP and event.key == pygame.locals.K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == pygame.locals.MOUSEMOTION:
                mousex, mousey = event.pos
            elif event.type == pygame.locals.MOUSEBUTTONUP:
                mousex, mousey = event.pos
                mouse_clicked = True

        box_x, box_y = get_box_at_pixel(mousex, mousey)
        if box_x is not None and box_y is not None:
            # The mouse is currently over a box
            if not revealed_boxes[box_x][box_y]:
                draw_highlight_box(box_x, box_y)
            if not revealed_boxes[box_x][box_y] and mouse_clicked:
                reveal_boxes_animation(main_board, [(box_x, box_y)])
                revealed_boxes[box_x][box_y] = True
                if first_selection[0] == -1 and first_selection[1] == -1:
                    first_selection = (box_x, box_y)
                else:
                    # Check if there is a match between the two icons
                    icon1shape, icon1color = get_shape_and_color(main_board, \
                        first_selection[0], first_selection[1])
                    icon2shape, icon2color = get_shape_and_color(main_board, box_x, box_y)

                    if icon1shape != icon2shape or icon1color != icon2color:
                        # Icons don't match
                        pygame.time.wait(1000)
                        cover_boxes_animation(main_board, \
                            [(first_selection[0], first_selection[1]), (box_x, box_y)])
                        revealed_boxes[first_selection[0]][first_selection[1]] = False
                        revealed_boxes[box_x][box_y] = False
                    elif has_won(revealed_boxes):
                        game_won_animation(main_board)
                        pygame.time.wait(2000)

                        # Reset the board
                        main_board = get_randomized_board()
                        revealed_boxes = generate_revealed_boxes_data(False)

                        # Show the fully unrevealed board
                        draw_board(main_board, revealed_boxes)
                        pygame.display.update()
                        pygame.time.wait(1000)

                        # Replay startgame animation
                        start_game_animation(main_board)
                    first_selection = (-1, -1)

        # Redraw the screen and wait a clock tick
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def generate_revealed_boxes_data(val):
    """Generates a list of lists of bool values"""
    revealed_boxes = []
    for _ in range(BOARDWIDTH):
        revealed_boxes.append([val] * BOARDHEIGHT)
    return revealed_boxes


def get_randomized_board():
    """Generates a list of lists of tuples"""
    # Get a list of every possible shape in every possible color
    icons = []
    for color in ALLCOLORS:
        for shape in ALLSHAPES:
            icons.append((shape, color))

    random.shuffle(icons)
    num_icons_used = int(BOARDHEIGHT * BOARDWIDTH / 2) # how many pairs of icons do we need
    icons = icons[:num_icons_used] * 2 # take only needed amount of cards out of all cards in icons
    random.shuffle(icons)

    # Create the board data structure, with randomply placed icons.
    board = []
    for _ in range(BOARDWIDTH):
        column = []
        for __ in range(BOARDHEIGHT):
            column.append(icons[0])
            del icons[0]
        board.append(column)
    return board


def split_into_groups_of(group_size, the_list):
    """
    Split a list into a list of lists
    where the inner lists have at most group_size number of items
    """
    result = []
    for i in range(0, len(the_list), group_size):
        result.append(the_list[i:i + group_size])
    return result


def left_top_coords_of_box(box_x, box_y):
    """Convert board coordinates to pixel coordinates"""
    left = box_x * (BOXSIZE + GAPSIZE) + XMARGIN
    top = box_y * (BOXSIZE + GAPSIZE) + YMARGIN
    return (left, top)


def get_box_at_pixel(x_coord, y_coord):
    """Find box coordinates from pixel coordinates"""
    for box_x in range(BOARDWIDTH):
        for box_y in range(BOARDHEIGHT):
            left, top = left_top_coords_of_box(box_x, box_y)
            box_rect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if box_rect.collidepoint(x_coord, y_coord):
                return (box_x, box_y)
    return (None, None)


def draw_icon(shape, color, box_x, box_y):
    """Draw an icon at the space whose coordinates are given in box_x and box_y"""
    quarter = int(BOXSIZE * 0.25)
    half = int(BOXSIZE * 0.5)

    left, top = left_top_coords_of_box(box_x, box_y)
    # Draw the shapes
    if shape == DONUT:
        pygame.draw.circle(DISPLAYSURF, color, (left + half, top + half), half - 5)
        pygame.draw.circle(DISPLAYSURF, BGCOLOR, (left + half, top + half), quarter - 5)
    elif shape == SQUARE:
        pygame.draw.rect(DISPLAYSURF, color, \
            (left + quarter, top + quarter, BOXSIZE - half, BOXSIZE - half))
    elif shape == DIAMOND:
        pygame.draw.polygon(DISPLAYSURF, color, \
            ((left + half, top), (left + BOXSIZE - 1, top + half), \
            (left + half, top + BOXSIZE - 1), (left, top + half)))
    elif shape == LINES:
        for i in range(0, BOXSIZE, 4):
            pygame.draw.line(DISPLAYSURF, color, \
                (left, top + i), (left + i, top))
            pygame.draw.line(DISPLAYSURF, color, \
                (left + i, top + BOXSIZE - 1), (left + BOXSIZE - 1, top + i))
    elif shape == OVAL:
        pygame.draw.ellipse(DISPLAYSURF, color, (left, top + quarter, BOXSIZE, half))


def get_shape_and_color(board, box_x, box_y):
    """
    shape value for x, y spot is stored in board[x][y][0]
    color value for x, y spot is stored in board[x][y][1]
    """
    return board[box_x][box_y][0], board[box_x][box_y][1]


def draw_box_covers(board, boxes, coverage):
    """
    Draws boxes being covered/revealed. "boxes" is a list
    of two lists, which have the x & y spot of the box.
    """
    for box in boxes:
        left, top = left_top_coords_of_box(box[0], box[1])
        pygame.draw.rect(DISPLAYSURF, BGCOLOR, (left, top, BOXSIZE, BOXSIZE))
        shape, color = get_shape_and_color(board, box[0], box[1])
        draw_icon(shape, color, box[0], box[1])
        if coverage > 0: # only draw the cover if there is a coverage
            pygame.draw.rect(DISPLAYSURF, BOXCOLOR, (left, top, coverage, BOXSIZE))
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def reveal_boxes_animation(board, boxes_to_reveal):
    """Do the box reveal animation"""
    for coverage in range(BOXSIZE, (-REVEALSPEED) - 1, -REVEALSPEED):
        draw_box_covers(board, boxes_to_reveal, coverage)


def cover_boxes_animation(board, boxes_to_cover):
    """Do the "box cover" animation"""
    for coverage in range(0, BOXSIZE + REVEALSPEED, REVEALSPEED):
        draw_box_covers(board, boxes_to_cover, coverage)


def draw_board(board, revealed):
    """Draws all of the boxes in their covered or revealed state."""
    for box_x in range(BOARDWIDTH):
        for box_y in range(BOARDHEIGHT):
            left, top = left_top_coords_of_box(box_x, box_y)
            if not revealed[box_x][box_y]:
                # Draw a covered box.
                pygame.draw.rect(DISPLAYSURF, BOXCOLOR, (left, top, BOXSIZE, BOXSIZE))
            else:
                # Draw the revelaed icon.
                shape, color = get_shape_and_color(board, box_x, box_y)
                draw_icon(shape, color, box_x, box_y)


def draw_highlight_box(box_x, box_y):
    """Make an outline around a box"""
    left, top = left_top_coords_of_box(box_x, box_y)
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, \
        (left - 5, top - 5, BOXSIZE + 10, BOXSIZE + 10), 4)


def start_game_animation(board):
    """Randomly reveal the boxes 8 at a time."""
    covered_boxes = generate_revealed_boxes_data(False) # [[False, False], [False, False]]
    boxes = []
    for num_x in range(BOARDWIDTH):
        for num_y in range(BOARDHEIGHT):
            boxes.append((num_x, num_y))
    random.shuffle(boxes)
    box_groups = split_into_groups_of(8, boxes)

    draw_board(board, covered_boxes)
    for box_group in box_groups:
        reveal_boxes_animation(board, box_group)
        cover_boxes_animation(board, box_group)


def game_won_animation(board):
    """Flash the background color when the player has won"""
    covered_boxes = generate_revealed_boxes_data(True)
    color1 = LIGHTBGCOLOR
    color2 = BGCOLOR

    for _ in range(13):
        color1, color2 = color2, color1
        DISPLAYSURF.fill(color1)
        draw_board(board, covered_boxes)
        pygame.display.update()
        pygame.time.wait(300)


def has_won(revealed_boxes):
    """Return True if all the boxes have been revealed, otherwise False"""
    for i in revealed_boxes:
        if False in i:
            return False
    return True


if __name__ == '__main__':
    main()
