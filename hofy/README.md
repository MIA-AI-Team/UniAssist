# AI Learning Platform - Database MVP

PostgreSQL schema for the demo version of an AI-enhanced university learning platform.

## Main Features

- Students, professors, and TAs
- Courses and course enrollment
- Lectures and lecture files
- RAG document chunks
- Assignments and submissions
- AI grading with detailed feedback
- AI-generated or staff-created rubrics
- Quizzes:
  - MCQ
  - Written questions
  - AI-generated questions
- AI tutoring chat
- Chat feedback
- Student topic mastery
- Personalized learning plans

## AI Context Flow

The backend can build an AI context using:

1. Student information
2. Current course
3. Current lecture
4. Student topic mastery
5. Learning plan
6. Recent chat/session summary
7. RAG-retrieved lecture chunks

Then the context is sent to the selected LLM such as an OpenAI or Anthropic model.

## RAG

Lecture files are split into chunks and embedded outside PostgreSQL in a vector database.

`document_chunks.vector_id` links a SQL record to its vector-store record.

## MVP Design Choices

Some data is intentionally stored as JSONB to avoid unnecessary tables during the demo:

- Rubric criteria
- AI evaluation details
- Learning plan

These can later be normalized into separate tables if the project grows.

## Suggested Demo Flow

Student:
Course -> Lecture -> Chat -> Feedback

Student:
Course -> Assignment -> Submission -> AI Evaluation

Professor:
Course -> Assignment -> AI-generated Rubric -> Accept/Edit

Student:
Quiz -> Attempt -> Answers -> Score

AI:
Student data + Mastery + Learning Plan + RAG -> Personalized response
