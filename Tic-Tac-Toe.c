#include <stdio.h>
#include <stdlib.h>

#define PLAYER1 'X'
#define PLAYER2 'O'
#define EMPTY ' '

void printBoard(char board[3][3]);
int checkWinner(char board[3][3]);
int alphaBeta(char board[3][3], int depth, int alpha, int beta, int isMaximizing);
int findBestMove(char board[3][3]);
int isMovesLeft(char board[3][3]);
void makeMove(char board[3][3], int move, char player);

int main() {
    char board[3][3] = {
        {EMPTY, EMPTY, EMPTY},
        {EMPTY, EMPTY, EMPTY},
        {EMPTY, EMPTY, EMPTY}
    };

    int mode;
    printf("Choose game mode:\n");
    printf("1. Player vs Player\n");
    printf("2. Player vs Computer\n");
    printf("Enter your choice (1 or 2): ");
    scanf("%d", &mode);

    if (mode != 1 && mode != 2) {
        printf("Invalid choice. Exiting...\n");
        return 1;
    }

    printf("Tic Tac Toe\n");
    printf("Player 1 is X and Player 2 is O.\n");

    while (1) {
        // Player 1's turn
        printBoard(board);
        int move;

        printf("Player 1 (X), enter your move (1-9): ");
        scanf("%d", &move);
        move--; // Adjust for 0-indexing

        if (move < 0 || move > 8 || board[move / 3][move % 3] != EMPTY) {
            printf("Invalid move. Try again.\n");
            continue;
        }

        makeMove(board, move, PLAYER1);

        if (checkWinner(board) == 1) {
            printBoard(board);
            printf("Player 1 wins!\n");
            break;
        } else if (!isMovesLeft(board)) {
            printBoard(board);
            printf("It's a draw!\n");
            break;
        }

        if (mode == 2) {
            // Player 2's turn (Computer using Alpha-Beta Pruning)
            printf("Player 2 (O) is making a move...\n");
            move = findBestMove(board);
            makeMove(board, move, PLAYER2);

            if (checkWinner(board) == -1) {
                printBoard(board);
                printf("Player 2 wins!\n");
                break;
            } else if (!isMovesLeft(board)) {
                printBoard(board);
                printf("It's a draw!\n");
                break;
            }
        } else {
            // Player 2's turn (Human)
            printBoard(board);
            printf("Player 2 (O), enter your move (1-9): ");
            scanf("%d", &move);
            move--; // Adjust for 0-indexing

            if (move < 0 || move > 8 || board[move / 3][move % 3] != EMPTY) {
                printf("Invalid move. Try again.\n");
                continue;
            }

            makeMove(board, move, PLAYER2);

            if (checkWinner(board) == -1) {
                printBoard(board);
                printf("Player 2 wins!\n");
                break;
            } else if (!isMovesLeft(board)) {
                printBoard(board);
                printf("It's a draw!\n");
                break;
            }
        }
    }

    return 0;
}

void printBoard(char board[3][3]) {
    printf("\n");
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            printf(" %c ", board[i][j]);
            if (j < 2) printf("|");
        }
        printf("\n");
        if (i < 2) printf("---|---|---\n");
    }
    printf("\n");
}

int checkWinner(char board[3][3]) {
    // Check rows and columns
    for (int i = 0; i < 3; i++) {
        if (board[i][0] == board[i][1] && board[i][1] == board[i][2]) {
            if (board[i][0] == PLAYER1) return 1; // Player 1 wins
            if (board[i][0] == PLAYER2) return -1; // Player 2 wins
        }
        if (board[0][i] == board[1][i] && board[1][i] == board[2][i]) {
            if (board[0][i] == PLAYER1) return 1; // Player 1 wins
            if (board[0][i] == PLAYER2) return -1; // Player 2 wins
        }
    }

    // Check diagonals
    if (board[0][0] == board[1][1] && board[1][1] == board[2][2]) {
        if (board[0][0] == PLAYER1) return 1; // Player 1 wins
        if (board[0][0] == PLAYER2) return -1; // Player 2 wins
    }
    if (board[0][2] == board[1][1] && board[1][1] == board[2][0]) {
        if (board[0][2] == PLAYER1) return 1; // Player 1 wins
        if (board[0][2] == PLAYER2) return -1; // Player 2 wins
    }

    return 0; // No winner
}

int alphaBeta(char board[3][3], int depth, int alpha, int beta, int isMaximizing) {
    int score = checkWinner(board);

    if (score == 1) return -10 + depth; // Player 1 wins
    if (score == -1) return 10 - depth; // Player 2 wins
    if (!isMovesLeft(board)) return 0; // Draw

    if (isMaximizing) {
        int bestVal = -1000;
        for (int i = 0; i < 9; i++) {
            if (board[i / 3][i % 3] == EMPTY) {
                board[i / 3][i % 3] = PLAYER2; // Simulate Player 2's move
                bestVal = (bestVal > alphaBeta(board, depth + 1, alpha, beta, 0)) ? bestVal : alphaBeta(board, depth + 1, alpha, beta, 0);
                board[i / 3][i % 3] = EMPTY;
                alpha = (alpha > bestVal) ? alpha : bestVal;
                if (beta <= alpha) break; // Beta cut-off
            }
        }
        return bestVal;
    } else {
        int bestVal = 1000;
        for (int i = 0; i < 9; i++) {
            if (board[i / 3][i % 3] == EMPTY) {
                board[i / 3][i % 3] = PLAYER1; // Simulate Player 1's move
                bestVal = (bestVal < alphaBeta(board, depth + 1, alpha, beta, 1)) ? bestVal : alphaBeta(board, depth + 1, alpha, beta, 1);
                board[i / 3][i % 3] = EMPTY;
                beta = (beta < bestVal) ? beta : bestVal;
                if (beta <= alpha) break; // Alpha cut-off
            }
        }
        return bestVal;
    }
}

int findBestMove(char board[3][3]) {
    int bestVal = -1000;
    int bestMove = -1;

    for (int i = 0; i < 9; i++) {
        if (board[i / 3][i % 3] == EMPTY) {
            board[i / 3][i % 3] = PLAYER2; // Simulate Player 2's move
            int moveVal = alphaBeta(board, 0, -1000, 1000, 0);
            board[i / 3][i % 3] = EMPTY; // Undo the move

            if (moveVal > bestVal) {
                bestMove = i;
                bestVal = moveVal;
            }
        }
    }

    return bestMove;
}

int isMovesLeft(char board[3][3]) {
    for (int i = 0; i < 9; i++) {
        if (board[i / 3][i % 3] == EMPTY) return 1; // There are moves left
    }
    return 0; // No moves left
}

void makeMove(char board[3][3], int move, char player) {
    board[move / 3][move % 3] = player;
}
