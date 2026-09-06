-- AI Learning Platform - MVP Database Schema
-- PostgreSQL
-- This schema is designed for a demo/MVP of an AI-enhanced university learning platform.
-- It covers students, courses, lectures, RAG documents, assignments, AI grading,
-- quizzes, AI tutoring chat, feedback, student mastery, and learning plans.

-- =========================================================
-- 1. USERS
-- Stores all system users: students, professors, and TAs.
-- =========================================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL
        CHECK (role IN ('student', 'professor', 'ta')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 2. STUDENTS
-- Academic information specific to students.
-- This data can be used when building AI context.
-- =========================================================
CREATE TABLE students (
    user_id BIGINT PRIMARY KEY
        REFERENCES users(id) ON DELETE CASCADE,
    student_number VARCHAR(50) UNIQUE NOT NULL,
    major VARCHAR(150),
    cohort_year INT
);

-- =========================================================
-- 3. COURSES
-- University subjects/courses.
-- =========================================================
CREATE TABLE courses (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 4. COURSE_STUDENTS
-- Many-to-many relationship between students and courses.
-- =========================================================
CREATE TABLE course_students (
    course_id BIGINT REFERENCES courses(id) ON DELETE CASCADE,
    student_id BIGINT REFERENCES students(user_id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, student_id)
);

-- =========================================================
-- 5. LECTURES
-- Lectures belonging to courses.
-- =========================================================
CREATE TABLE lectures (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title VARCHAR(250) NOT NULL,
    description TEXT,
    lecture_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 6. FILES
-- Uploaded files such as lecture PDFs or student submissions.
-- The actual file is stored outside PostgreSQL.
-- =========================================================
CREATE TABLE files (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    lecture_id BIGINT REFERENCES lectures(id) ON DELETE CASCADE,
    uploaded_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 7. DOCUMENT_CHUNKS
-- Chunks extracted from lecture documents for RAG.
-- vector_id points to the corresponding vector in a vector DB.
-- =========================================================
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    vector_id VARCHAR(255),
    embedding_model VARCHAR(150),
    UNIQUE(file_id, chunk_index)
);

-- =========================================================
-- 8. ASSIGNMENTS
-- Assignments created by professors/TAs.
-- =========================================================
CREATE TABLE assignments (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    created_by BIGINT NOT NULL REFERENCES users(id),
    title VARCHAR(250) NOT NULL,
    description TEXT,
    assignment_type VARCHAR(50)
        CHECK (assignment_type IN ('coding', 'research', 'pdf', 'text', 'mixed')),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 9. SUBMISSIONS
-- Student submission for an assignment.
-- Supports direct text answers and uploaded files.
-- =========================================================
CREATE TABLE submissions (
    id BIGSERIAL PRIMARY KEY,
    assignment_id BIGINT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(user_id),
    attempt_number INT DEFAULT 1,
    answer_text TEXT,
    file_id BIGINT REFERENCES files(id),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'ai_graded', 'final')),
    UNIQUE(assignment_id, student_id, attempt_number)
);

-- =========================================================
-- 10. RUBRICS
-- Rubrics can be AI-generated or staff-created.
-- criteria is JSONB to keep the MVP simple.
-- =========================================================
CREATE TABLE rubrics (
    id BIGSERIAL PRIMARY KEY,
    assignment_id BIGINT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    version INT DEFAULT 1,
    source VARCHAR(30)
        CHECK (source IN ('ai_generated', 'staff_created')),
    status VARCHAR(30)
        CHECK (status IN ('pending', 'accepted', 'rejected')),
    criteria JSONB NOT NULL,
    created_by BIGINT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 11. AI_EVALUATIONS
-- Stores detailed AI grading results for submissions.
-- details contains criterion-level scores and feedback.
-- =========================================================
CREATE TABLE ai_evaluations (
    id BIGSERIAL PRIMARY KEY,
    submission_id BIGINT NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    rubric_id BIGINT REFERENCES rubrics(id),
    model_name VARCHAR(150),
    total_score NUMERIC(6,2),
    overall_feedback TEXT,
    strengths TEXT,
    weaknesses TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 12. QUIZZES
-- Quizzes inside courses, optionally connected to a lecture.
-- =========================================================
CREATE TABLE quizzes (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    lecture_id BIGINT REFERENCES lectures(id),
    created_by BIGINT REFERENCES users(id),
    title VARCHAR(250) NOT NULL,
    description TEXT,
    duration_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 13. QUIZ_QUESTIONS
-- Supports MCQ and written questions.
-- Questions may be created by staff or generated by AI.
-- =========================================================
CREATE TABLE quiz_questions (
    id BIGSERIAL PRIMARY KEY,
    quiz_id BIGINT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(30) NOT NULL
        CHECK (question_type IN ('mcq', 'written')),
    points NUMERIC(6,2) NOT NULL,
    source VARCHAR(30) NOT NULL
        CHECK (source IN ('staff', 'ai_generated')),
    model_name VARCHAR(150),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 14. QUIZ_OPTIONS
-- Answer choices for MCQ questions.
-- =========================================================
CREATE TABLE quiz_options (
    id BIGSERIAL PRIMARY KEY,
    question_id BIGINT NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE
);

-- =========================================================
-- 15. QUIZ_ATTEMPTS
-- One student's attempt at a quiz.
-- =========================================================
CREATE TABLE quiz_attempts (
    id BIGSERIAL PRIMARY KEY,
    quiz_id BIGINT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(user_id),
    started_at TIMESTAMP,
    submitted_at TIMESTAMP,
    score NUMERIC(6,2),
    status VARCHAR(30) DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'submitted', 'graded'))
);

-- =========================================================
-- 16. QUIZ_ANSWERS
-- Stores MCQ selections or written answers.
-- AI feedback can be stored for written questions.
-- =========================================================
CREATE TABLE quiz_answers (
    id BIGSERIAL PRIMARY KEY,
    attempt_id BIGINT NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id BIGINT NOT NULL REFERENCES quiz_questions(id),
    selected_option_id BIGINT REFERENCES quiz_options(id),
    answer_text TEXT,
    score NUMERIC(6,2),
    ai_feedback TEXT
);

-- =========================================================
-- 17. CHAT_SESSIONS
-- A conversation between a student and the AI tutor.
-- The session may be associated with a course and lecture.
-- summary and understanding_score provide lightweight memory.
-- =========================================================
CREATE TABLE chat_sessions (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(user_id),
    course_id BIGINT NOT NULL REFERENCES courses(id),
    lecture_id BIGINT REFERENCES lectures(id),
    summary TEXT,
    understanding_score NUMERIC(5,2),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

-- =========================================================
-- 18. CHAT_MESSAGES
-- Every student/AI message in a chat session.
-- =========================================================
CREATE TABLE chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL
        CHECK (sender_type IN ('student', 'ai')),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 19. CHAT_FEEDBACK
-- Student feedback about an AI tutoring session.
-- Used to evaluate helpfulness and understanding.
-- =========================================================
CREATE TABLE chat_feedback (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    helpful BOOLEAN,
    understood BOOLEAN,
    confusion_level INT CHECK (confusion_level BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 20. TOPICS
-- Concepts/topics inside a course.
-- Used for personalized learning.
-- =========================================================
CREATE TABLE topics (
    id BIGSERIAL PRIMARY KEY,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    UNIQUE(course_id, name)
);

-- =========================================================
-- 21. STUDENT_MASTERY
-- Estimated mastery of each topic for each student.
-- This is an important input to the AI context.
-- =========================================================
CREATE TABLE student_mastery (
    student_id BIGINT REFERENCES students(user_id) ON DELETE CASCADE,
    topic_id BIGINT REFERENCES topics(id) ON DELETE CASCADE,
    mastery_score NUMERIC(5,2) CHECK (mastery_score BETWEEN 0 AND 100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, topic_id)
);

-- =========================================================
-- 22. LEARNING_PLANS
-- Personalized learning plan for a student in a course.
-- plan is JSONB to keep the MVP simple.
-- =========================================================
CREATE TABLE learning_plans (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES students(user_id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    plan JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
