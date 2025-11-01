-- ============================================
-- STORED PROCEDURES AND TRIGGERS
-- Database: studentperformancedb
-- ============================================

-- ============================================
-- STORED PROCEDURE 1: Get Complete Student Profile
-- Purpose: Fetch all student information with related data in one call
-- ============================================
CREATE OR REPLACE FUNCTION get_student_full_profile(p_student_id UUID)
RETURNS TABLE(
    student_id UUID,
    age INTEGER,
    sex VARCHAR,
    address VARCHAR,
    famsize VARCHAR,
    pstatus VARCHAR,
    -- Family background
    medu INTEGER,
    fedu INTEGER,
    mjob VARCHAR,
    fjob VARCHAR,
    guardian VARCHAR,
    fanrel INTEGER,
    -- School info
    school VARCHAR,
    reason VARCHAR,
    traveltime INTEGER,
    studytime INTEGER,
    failures INTEGER,
    schoolsup BOOLEAN,
    famsup BOOLEAN,
    paid BOOLEAN,
    -- Academic records
    subject VARCHAR,
    absences INTEGER,
    g1 INTEGER,
    g2 INTEGER,
    g3 INTEGER,
    romantic BOOLEAN,
    freetime INTEGER,
    goodt INTEGER,
    -- Composite scores (calculated)
    at_risk BOOLEAN,
    socioeconomic_score NUMERIC,
    support_systems NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.student_id,
        s.age,
        s.sex,
        s.address,
        s.famsize,
        s.pstatus,
        -- Family background
        fb.medu,
        fb.fedu,
        fb.mjob,
        fb.fjob,
        fb.guardian,
        fb.fanrel,
        -- School info
        si.school,
        si.reason,
        si.traveltime,
        si.studytime,
        si.failures,
        si.schoolsup,
        si.famsup,
        si.paid,
        -- Academic records
        ar.subject,
        ar.absences,
        ar.g1,
        ar.g2,
        ar.g3,
        ar.romantic,
        ar.freetime,
        ar.goodt,
        -- Calculated composite scores
        (ar.g3 < 10)::BOOLEAN as at_risk,
        ((fb.medu + fb.fedu) / 2.0)::NUMERIC(5,2) as socioeconomic_score,
        ((CASE WHEN si.schoolsup THEN 1 ELSE 0 END + 
          CASE WHEN si.famsup THEN 1 ELSE 0 END + 
          CASE WHEN si.paid THEN 1 ELSE 0 END) / 3.0)::NUMERIC(5,2) as support_systems
    FROM students s
    LEFT JOIN family_background fb ON s.student_id = fb.student_id
    LEFT JOIN school_info si ON s.student_id = si.student_id
    LEFT JOIN academic_records ar ON s.student_id = ar.student_id
    WHERE s.student_id = p_student_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED PROCEDURE 2: Calculate Student Risk Score
-- Purpose: Calculate a risk score based on multiple factors
-- Returns a score from 0-100 (higher = more at risk)
-- ============================================
CREATE OR REPLACE FUNCTION calculate_student_risk_score(p_student_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    risk_score NUMERIC := 0;
    v_failures INTEGER;
    v_absences INTEGER;
    v_g1 INTEGER;
    v_g2 INTEGER;
    v_g3 INTEGER;
    v_goodt INTEGER;
    v_studytime INTEGER;
    v_freetime INTEGER;
BEGIN
    -- Fetch academic and school data (joined)
    SELECT 
        si.failures, ar.absences, ar.g1, ar.g2, ar.g3,
        ar.goodt, si.studytime, ar.freetime
    INTO 
        v_failures, v_absences, v_g1, v_g2, v_g3,
        v_goodt, v_studytime, v_freetime
    FROM academic_records ar
    INNER JOIN school_info si ON ar.student_id = si.student_id
    WHERE ar.student_id = p_student_id;
    
    -- If no record found, return NULL
    IF NOT FOUND THEN
        RETURN NULL;
    END IF;
    
    -- Calculate risk score components
    
    -- 1. Grade performance (30 points max)
    IF v_g3 < 10 THEN
        risk_score := risk_score + 30;
    ELSIF v_g3 < 12 THEN
        risk_score := risk_score + 20;
    ELSIF v_g3 < 14 THEN
        risk_score := risk_score + 10;
    END IF;
    
    -- 2. Grade trend (15 points max)
    IF v_g1 > 0 AND v_g2 > 0 AND v_g3 > 0 THEN
        IF (v_g3 - v_g1) < -5 THEN
            risk_score := risk_score + 15;  -- Declining significantly
        ELSIF (v_g3 - v_g1) < 0 THEN
            risk_score := risk_score + 10;  -- Declining
        END IF;
    END IF;
    
    -- 3. Failures (20 points max)
    risk_score := risk_score + LEAST(v_failures * 7, 20);
    
    -- 4. Absences (15 points max)
    IF v_absences > 20 THEN
        risk_score := risk_score + 15;
    ELSIF v_absences > 10 THEN
        risk_score := risk_score + 10;
    ELSIF v_absences > 5 THEN
        risk_score := risk_score + 5;
    END IF;
    
    -- 5. Free time and social behavior (10 points max)
    IF v_freetime > 3 THEN
        risk_score := risk_score + 5;
    END IF;
    
    IF v_goodt > 3 THEN
        risk_score := risk_score + 5;
    ELSIF v_goodt > 2 THEN
        risk_score := risk_score + 3;
    END IF;
    
    -- 7. Study time (5 points - inverse, less study = more risk)
    IF v_studytime = 1 THEN
        risk_score := risk_score + 5;
    ELSIF v_studytime = 2 THEN
        risk_score := risk_score + 3;
    END IF;
    
    -- Cap at 100
    risk_score := LEAST(risk_score, 100);
    
    RETURN risk_score;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED PROCEDURE 3: Get Students Performance Summary
-- Purpose: Get summary statistics of student performance
-- ============================================
CREATE OR REPLACE FUNCTION get_students_performance_summary()
RETURNS TABLE(
    total_students INTEGER,
    at_risk_count INTEGER,
    not_at_risk_count INTEGER,
    avg_g3 NUMERIC,
    avg_absences NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_students,
        COUNT(CASE WHEN ar.g3 < 10 THEN 1 END)::INTEGER as at_risk_count,
        COUNT(CASE WHEN ar.g3 >= 10 THEN 1 END)::INTEGER as not_at_risk_count,
        AVG(ar.g3)::NUMERIC(5,2) as avg_g3,
        AVG(ar.absences)::NUMERIC(5,2) as avg_absences
    FROM academic_records ar;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STORED PROCEDURE 4: Get Students by Risk Level
-- Purpose: Get list of students filtered by risk score range
-- ============================================
CREATE OR REPLACE FUNCTION get_students_by_risk_level(
    min_risk INTEGER DEFAULT 0,
    max_risk INTEGER DEFAULT 100,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    student_id UUID,
    age INTEGER,
    sex VARCHAR,
    g1 INTEGER,
    g2 INTEGER,
    g3 INTEGER,
    at_risk BOOLEAN,
    risk_score NUMERIC,
    failures INTEGER,
    absences INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.student_id,
        s.age,
        s.sex,
        ar.g1,
        ar.g2,
        ar.g3,
        (ar.g3 < 10)::BOOLEAN as at_risk,
        calculate_student_risk_score(s.student_id) as risk_score,
        si.failures,
        ar.absences
    FROM students s
    INNER JOIN academic_records ar ON s.student_id = ar.student_id
    INNER JOIN school_info si ON s.student_id = si.student_id
    WHERE calculate_student_risk_score(s.student_id) BETWEEN min_risk AND max_risk
    ORDER BY calculate_student_risk_score(s.student_id) DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGER 1: Auto-update audit log on student changes
-- Purpose: Automatically log all changes to students table
-- ============================================
CREATE OR REPLACE FUNCTION audit_student_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (
            student_id, 
            action, 
            old_data, 
            changed_by,
            changed_at
        )
        VALUES (
            OLD.student_id,
            'DELETE',
            row_to_json(OLD),
            current_user,
            NOW()
        );
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (
            student_id,
            action,
            old_data,
            new_data,
            changed_by,
            changed_at
        )
        VALUES (
            NEW.student_id,
            'UPDATE',
            row_to_json(OLD),
            row_to_json(NEW),
            current_user,
            NOW()
        );
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (
            student_id,
            action,
            new_data,
            changed_by,
            changed_at
        )
        VALUES (
            NEW.student_id,
            'INSERT',
            row_to_json(NEW),
            current_user,
            NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on students table
DROP TRIGGER IF EXISTS students_audit_trigger ON students;
CREATE TRIGGER students_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON students
    FOR EACH ROW
    EXECUTE FUNCTION audit_student_changes();

-- ============================================
-- TRIGGER 2: Validate grade ranges
-- Purpose: Validate that grades are within acceptable range (0-20)
-- ============================================
CREATE OR REPLACE FUNCTION validate_grade_ranges()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate grade ranges (0-20)
    IF NEW.g1 IS NOT NULL AND (NEW.g1 < 0 OR NEW.g1 > 20) THEN
        RAISE EXCEPTION 'Grade G1 must be between 0 and 20, got %', NEW.g1;
    END IF;
    
    IF NEW.g2 IS NOT NULL AND (NEW.g2 < 0 OR NEW.g2 > 20) THEN
        RAISE EXCEPTION 'Grade G2 must be between 0 and 20, got %', NEW.g2;
    END IF;
    
    IF NEW.g3 IS NOT NULL AND (NEW.g3 < 0 OR NEW.g3 > 20) THEN
        RAISE EXCEPTION 'Grade G3 must be between 0 and 20, got %', NEW.g3;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on academic_records table
DROP TRIGGER IF EXISTS academic_records_validation_trigger ON academic_records;
CREATE TRIGGER academic_records_validation_trigger
    BEFORE INSERT OR UPDATE ON academic_records
    FOR EACH ROW
    EXECUTE FUNCTION validate_grade_ranges();

-- ============================================
-- TRIGGER 3: Auto-update timestamps
-- Purpose: Automatically update updated_at timestamp on record changes
-- ============================================
CREATE OR REPLACE FUNCTION update_modified_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on students table for timestamp updates
DROP TRIGGER IF EXISTS students_update_timestamp ON students;
CREATE TRIGGER students_update_timestamp
    BEFORE UPDATE ON students
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_timestamp();

-- ============================================
-- USAGE EXAMPLES
-- ============================================

/*
-- Example 1: Get complete student profile
SELECT * FROM get_student_full_profile('2da54d11-5d06-4fdd-b962-2b3bfbd47a61');

-- Example 2: Calculate risk score for a student
SELECT calculate_student_risk_score('2da54d11-5d06-4fdd-b962-2b3bfbd47a61');

-- Example 3: Update all students' at_risk status
SELECT * FROM update_all_students_at_risk_status();

-- Example 4: Get high-risk students (risk score 50-100)
SELECT * FROM get_students_by_risk_level(50, 100, 20);

-- Example 5: Get low-risk students (risk score 0-30)
SELECT * FROM get_students_by_risk_level(0, 30, 20);

-- Example 6: Check audit log after making changes
UPDATE students SET age = 19 WHERE student_id = '2da54d11-5d06-4fdd-b962-2b3bfbd47a61';
SELECT * FROM audit_log WHERE student_id = '2da54d11-5d06-4fdd-b962-2b3bfbd47a61' ORDER BY changed_at DESC LIMIT 5;

-- Example 7: Test grade validation (this will fail with error)
-- UPDATE academic_records SET g3 = 25 WHERE student_id = 'some-uuid';  -- Will raise exception

-- Example 8: Test automatic at_risk flag calculation
UPDATE academic_records SET g3 = 8 WHERE student_id = '2da54d11-5d06-4fdd-b962-2b3bfbd47a61';
-- at_risk should automatically be set to TRUE

UPDATE academic_records SET g3 = 15 WHERE student_id = '2da54d11-5d06-4fdd-b962-2b3bfbd47a61';
-- at_risk should automatically be set to FALSE
*/
