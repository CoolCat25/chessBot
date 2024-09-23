#formatting time


#make starting board positions
startingboard = ["r", "n", "b", "q", "k", "b", "n", "r", "p", "p", "p", "p", "p", "p", "p", "p"]
for i in range (0,32):
 startingboard.append(" ")
x = ["P", "P", "P", "P", "P", "P", "P", "P", "R", "N", "B", "Q", "K", "B", "N", "R"]
startingboard.extend(x)

#apply starting board to current board
currentboard = startingboard


#set pieces and piece values
pieces = ["r", "n", "b", "q", "k", "p", "R", "N", "B", "Q", "K", "P", " "]
pieces_white = ["r", "n", "b", "q", "k", "p"]
pieces_black = ["P", "R", "N", "B", "Q", "K"]
piece_values = [5, 3, 3, 9, 2000, 1, -5, -3, -3, -9, -2000, -1, 0]


#set square names
name_x = []
temp = ["a", "b", "c", "d", "e", "f", "g", "h"]
for i in range (64):
    name_x.extend(temp)
name_y = []
temp = ["1", "2", "3", "4", "5", "6", "7", "8"]
for i in range (8):
    for w in range (8):
        name_y.extend(temp[i])
full_names = []
for i in range (64):
    temp = name_x[i] + name_y[i]
    full_names.append(temp)



#evaluate the board
def evaluate_board():
    ev = 0
    for i in range (64):
        ev = ev + piece_values[pieces.index(currentboard[i])]
    return(ev)


#print the inputted list as a chess board
def print_board(listToPrint):
    #prints the inputted list in a chess board
    for i in range(8):
        print("")
        print(end="|")
        for w in range(8):
            print(listToPrint[(i * 8) + w] + " | ", end=" ")
    print("")


#move a piece from one position to another, inputs are list indexs, so beginning at 0
def move_piece(pos_1, pos_2):
    temp = currentboard[pos_1]
    currentboard[pos_1] = " "
    currentboard[pos_2] = temp


#work in progress, but will eventually calculate all white moves possible on the current board.
def find_white_moves():
    print()


#finds all possible white moves - STARTING JUMPS NOT YET INCLUDED
def white_pawn_moves(board):
    temp = []
    for i in range (64):
        if board[i] == "p":
            temp.append(i)
    temp_pawn = []
    for i in range (len(temp)):
        if board[temp[i]+8] == " ":
            temp_pawn.append(full_names[temp[i]] + full_names[temp[i]+8])
        if board[temp[i]+9] in pieces_black and full_names[temp[i]][0] != "h":
            temp_pawn.append(full_names[temp[i]] + full_names[temp[i] + 9])
        if board[temp[i]+7] in pieces_black and full_names[temp[i]][0] != "a":
            temp_pawn.append(full_names[temp[i]] + full_names[temp[i] + 7])

    return temp_pawn


#calculates white knight moves - to fix - the knight can move off the left and right of the board
def white_knight_moves(board):
    temp = []
    for i in range (64):
        if board[i] == "n":
            temp.append(i)
    temp_knight = []
    for i in range (len(temp)):
        if full_names[temp[i]][0] != "a" and full_names[temp[i]][1] != "8" and full_names[temp[i]][1] != "7" and board[temp[i]+15] == " " or board[temp[i]+15] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i]+15])
        if full_names[temp[i]][0] != "h" and full_names[temp[i]][1] != "8" and full_names[temp[i]][1] != "7" and board[temp[i] + 17] == " " or board[temp[i]+17] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i]+17])
        if full_names[temp[i]][0] != "h" and full_names[temp[i]][1] != "1" and full_names[temp[i]][1] != "2" and board[temp[i]-15] == " " or board[temp[i]-15] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i]-15])
        if full_names[temp[i]][0] != "a" and full_names[temp[i]][1] != "8" and full_names[temp[i]][1] != "7" and board[temp[i]-17] == " " or board[temp[i]-17] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i]-17])
        if full_names[temp[i]][0] != "g" and full_names[temp[i]][0] != "h" and board[temp[i]+10] == " " or board[temp[i]+10] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i]+10])
        if full_names[temp[i]][0] != "a" and full_names[temp[i]][0] != "b" and board[temp[i] + 6] == " " or board[temp[i] + 6] in pieces_black:
            temp_knight.append(full_names[temp[i]] + full_names[temp[i] + 6])
    return temp_knight

#completely broken :) needs fixing: moving across the sides of the board
def white_bishop_moves(board):
    temp = []
    for i in range (64):
        if board[i] == "b":
            temp.append(i)
    temp_bishop = []
    for i in range (len(temp)):
        for j in range (1,8):
            if full_names[temp[i]+(j*9)][0] != "a" and board[temp[i]+(j*9)] == " " or board[temp[i]+(j*9)] in pieces_black:
                if board[temp[i]+(j*9)] in pieces_black:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i] + (j * 9)])
                    break
                else:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i]+(j*9)])
            else:
                break
        for j in range (1,8):
            if  board[temp[i]+(j*7)] == " " or board[temp[i]+(j*7)] in pieces_black:
                if board[temp[i]+(j*7)] in pieces_black:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i] + (j * 7)]) #horrible code right here, will fix eventually
                    break
                else:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i]+(j*7)])
            else:
                break

        for j in range (1,8):
            if board[temp[i]+(j*-9)] == " " or board[temp[i]+(j*-9)] in pieces_black:
                if board[temp[i]+(j*-9)] in pieces_black:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i] + (j * -9)])
                    break
                else:
                    temp_bishop.append(full_names[temp[i]] + full_names[temp[i]+(j*-9)])
            else:
                break


#        if full_names[temp[i]][0] != "a" and currentboard[temp[i]+15] == " " or currentboard[temp[i]+15] in pieces_black:
#            temp_bishop.append(full_names[temp[i]] + full_names[temp[i]+15])
#        if full_names[temp[i]][0] != "h" and currentboard[temp[i] + 17] == " " or currentboard[temp[i] + 17] in pieces_black:
#            temp_bishop.append(full_names[temp[i]] + full_names[temp[i] + 17])
    return temp_bishop