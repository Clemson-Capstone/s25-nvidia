# Implementation-Assignment.pdf - 0

Page 1
CPSC 1900 – Implement an Autograder
Before starting this assignment, you should read the 1010 lab document and look at the
examples for phrases that should appear in student code output.
In this assingment, you will learn how to implement test cases in an autograder for an old 
CPSC 1010 Lab. As a reminder, this lab has students create a program that takes in 9 numbers 
for a 3x3 grid to check if the given numbers result in a magic square (a set of numbers is a 
magic square if given a set of numbers whose values are between 1 and n2 where the rows, 
columns, and diagonals sum to the same value). In the case of our 3x3 sets, they should all sum 
to 15. 
In total, your autograder will have 7 test cases, but the first two (cases 0 and 1) are included in 
the autograder template. 
• Modify the files array to include all expected files (code file and makefile)
• Modify the test_Menu test case
o Change the expectedArr array to include phrase(s) from the Lab’s prompt.
• Write test cases 3-6:
o Test case 3
 Give it a short but descriptive function name and test case description
 Program input: 1 2 3 4 5 6 7 8 9
 Check if their program outputs:
• The rows that do not sum to 15
• The columns that do not sum to 15
• That it is not a magic square
• Other output that should always be printed out
o i.e. “Analyzing…”
o Test case 4
 Give it a short but descriptive function name and test case description
 Program input: 4 9 2 3 5 7 8 1 6
 Check if their program outputs:
• That is a magic square
• Other output that should always be printed out
o Test case 5
 Give it a short but descriptive function name and test case description
 Program input: 2 7 6 9 5 1 4 3 8
 Check if their program outputs:
• That it is a magic square
• Other output that should always be printed out
o Test case 6
 Give it a short but descriptive function name and test case description
 Program input: 9 1 5 9 4 7 7 4 4
 Check if their program outputs: