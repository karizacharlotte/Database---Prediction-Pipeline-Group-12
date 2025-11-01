-- PostgreSQL Schema for Student Performance Database
-- Database: studentperformancedb
-- Tables: students, academic_records, family_background, school_info, student_audit_log

-- ============================================
-- Table: students (Main student information)
-- ============================================
CREATE TABLE IF NOT EXISTS students (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    age INTEGER CHECK (age >= 15 AND age <= 25),
    sex VARCHAR(1) CHECK (sex IN ('M', 'F')),
    address VARCHAR(1) CHECK (address IN ('U', 'R')),  -- U=Urban, R=Rural
    famsize VARCHAR(3) CHECK (famsize IN ('LE3', 'GT3')),  -- LE3: <=3, GT3: >3
    pstatus VARCHAR(1) CHECK (pstatus IN ('T', 'A')),  -- T=Together, A=Apart
    school VARCHAR(5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Table: family_background (Family-related data)
-- ============================================
CREATE TABLE IF NOT EXISTS family_background (
    family_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    medu INTEGER CHECK (medu >= 0 AND medu <= 4),  -- Mother's education
    fedu INTEGER CHECK (fedu >= 0 AND fedu <= 4),  -- Father's education
    mjob VARCHAR(20),  -- Mother's job
    fjob VARCHAR(20),  -- Father's job
    reason VARCHAR(20),  -- Reason to choose this school
    guardian VARCHAR(10),
    traveltime INTEGER CHECK (traveltime >= 1 AND traveltime <= 4),
    famrel INTEGER CHECK (famrel >= 1 AND famrel <= 5),  -- Family relationship quality
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Table: academic_records (Academic performance)
-- ============================================
CREATE TABLE IF NOT EXISTS academic_records (
    record_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    studytime INTEGER CHECK (studytime >= 1 AND studytime <= 4),
    failures INTEGER CHECK (failures >= 0 AND failures <= 4),
    schoolsup BOOLEAN,  -- Extra educational support
    famsup BOOLEAN,  -- Family educational support
    paid BOOLEAN,  -- Extra paid classes
    activities BOOLEAN,  -- Extra-curricular activities
    nursery BOOLEAN,  -- Attended nursery school
    higher BOOLEAN,  -- Wants higher education
    internet BOOLEAN,  -- Internet access at home
    romantic BOOLEAN,  -- In a romantic relationship
    freetime INTEGER CHECK (freetime >= 1 AND freetime <= 5),
    goout INTEGER CHECK (goout >= 1 AND goout <= 5),
    dalc INTEGER CHECK (dalc >= 1 AND dalc <= 5),  -- Workday alcohol consumption
    walc INTEGER CHECK (walc >= 1 AND walc <= 5),  -- Weekend alcohol consumption
    health INTEGER CHECK (health >= 1 AND health <= 5),
    absences INTEGER CHECK (absences >= 0),
    g1 INTEGER CHECK (g1 >= 0 AND g1 <= 20),  -- First period grade
    g2 INTEGER CHECK (g2 >= 0 AND g2 <= 20),  -- Second period grade
    g3 INTEGER CHECK (g3 >= 0 AND g3 <= 20),  -- Final grade
    at_risk BOOLEAN,  -- Computed: TRUE if G3 < 10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Table: school_info (School-related information)
-- ============================================
CREATE TABLE IF NOT EXISTS school_info (
    school_info_id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    school_name VARCHAR(10),
    school_support BOOLEAN,
    family_support BOOLEAN,
    paid_classes BOOLEAN,
    activities BOOLEAN,
    nursery BOOLEAN,
    higher_ed_aspiration BOOLEAN,
    internet_access BOOLEAN,
    romantic_relationship BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- Table: student_audit_log (Audit trail)
-- ============================================
CREATE TABLE IF NOT EXISTS student_audit_log (
    log_id SERIAL PRIMARY KEY,
    student_id INTEGER,  -- Can be NULL if student deleted
    action VARCHAR(20) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100)
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_students_school ON students(school);
CREATE INDEX IF NOT EXISTS idx_students_sex ON students(sex);
CREATE INDEX IF NOT EXISTS idx_family_student ON family_background(student_id);
CREATE INDEX IF NOT EXISTS idx_academic_student ON academic_records(student_id);
CREATE INDEX IF NOT EXISTS idx_academic_atrisk ON academic_records(at_risk);
CREATE INDEX IF NOT EXISTS idx_school_info_student ON school_info(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_student ON student_audit_log(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON student_audit_log(action);

-- ============================================
-- Comments for Documentation
-- ============================================
COMMENT ON TABLE students IS 'Main student demographic information';
COMMENT ON TABLE family_background IS 'Family-related attributes including parental education and jobs';
COMMENT ON TABLE academic_records IS 'Academic performance metrics and lifestyle factors';
COMMENT ON TABLE school_info IS 'School-related support and activity information';
COMMENT ON TABLE student_audit_log IS 'Audit trail for all changes to student records';
