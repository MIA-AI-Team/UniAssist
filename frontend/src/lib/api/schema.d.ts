export interface paths {
    "/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_auth_me_patch"];
        trace?: never;
    };
    "/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Users */
        get: operations["users_admin_users_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** User Detail */
        get: operations["user_detail_admin_users__user_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Correct */
        patch: operations["correct_admin_users__user_id__patch"];
        trace?: never;
    };
    "/admin/audit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Audit */
        get: operations["audit_admin_audit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/ai-metrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Metrics */
        get: operations["metrics_admin_ai_metrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List All
         * @description List tasks. Students automatically filter by their cohort + major and if the task is not due.
         *     Staff can see all tasks or filter manually.
         */
        get: operations["list_all_tasks__get"];
        put?: never;
        /**
         * Create
         * @description Professor or TA creates a new task.
         */
        post: operations["create_tasks__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/submissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Task Submissions */
        get: operations["task_submissions_tasks__task_id__submissions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get One
         * @description Get a single task with its type-specific details.
         */
        get: operations["get_one_tasks__task_id__get"];
        put?: never;
        post?: never;
        /**
         * Delete
         * @description Professor deletes a task.
         *     Cascades to all related rows: rubrics, submissions, files, chat sessions.
         *     TAs cannot delete tasks.
         */
        delete: operations["delete_tasks__task_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/files/upload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Upload
         * @description Upload a file and store it in the FILES table.
         *
         *     purpose=reference  → lab PDF uploaded by staff, linked to a task
         *     purpose=submission → student submission file
         */
        post: operations["upload_files_upload_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/files/{file_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get File Info
         * @description Retrieve metadata about an uploaded file.
         */
        get: operations["get_file_info_files__file_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/files/{file_id}/download": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Download File
         * @description Download the actual file payload.
         *
         *     Students can only download their own files or reference files
         *     linked to tasks they have access to. Staff can download any file.
         */
        get: operations["download_file_files__file_id__download_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Submit
         * @description Student submits work for a task.
         */
        post: operations["submit_submissions__post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/my/{task_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Submissions
         * @description Student views all their submissions for a task.
         */
        get: operations["my_submissions_submissions_my__task_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}/grade": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Grade
         * @description Staff triggers AI grading for a submission.
         */
        post: operations["grade_submissions__submission_id__grade_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/submissions/{submission_id}/confirm": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Confirm
         * @description Professor confirms or overrides the AI-suggested grade.
         */
        patch: operations["confirm_submissions__submission_id__confirm_patch"];
        trace?: never;
    };
    "/submissions/{submission_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get One
         * @description Get submission details including grade and code reviews.
         */
        get: operations["get_one_submissions__submission_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/rubrics/suggest": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Suggest
         * @description Staff triggers AI to suggest a rubric.
         */
        post: operations["suggest_tasks__task_id__rubrics_suggest_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/rubrics/refine": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Refine
         * @description Staff provides feedback and AI creates a refined rubric version.
         */
        post: operations["refine_tasks__task_id__rubrics_refine_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/rubrics/create": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Create
         * @description Staff manually creates a rubric (no AI involved).
         */
        post: operations["create_tasks__task_id__rubrics_create_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/rubrics/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Update Status
         * @description Professor accepts or rejects a rubric.
         */
        patch: operations["update_status_tasks__task_id__rubrics_status_patch"];
        trace?: never;
    };
    "/tasks/{task_id}/rubrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List All Rubrics
         * @description List all rubric versions for a task.
         */
        get: operations["list_all_rubrics_tasks__task_id__rubrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/chat-sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Sessions */
        get: operations["sessions_tasks__task_id__chat_sessions_get"];
        put?: never;
        /** Create */
        post: operations["create_tasks__task_id__chat_sessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_chat_sessions__session_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-sessions/{session_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Messages */
        get: operations["messages_chat_sessions__session_id__messages_get"];
        put?: never;
        /** Send */
        post: operations["send_chat_sessions__session_id__messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-sessions/{session_id}/legacy-messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Legacy */
        get: operations["legacy_chat_sessions__session_id__legacy_messages_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-sessions/{session_id}/share-preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Preview */
        get: operations["preview_chat_sessions__session_id__share_preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-sessions/{session_id}/shares": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Owner Shares */
        get: operations["owner_shares_chat_sessions__session_id__shares_get"];
        put?: never;
        /** Share */
        post: operations["share_chat_sessions__session_id__shares_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-shares/{share_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Shared Detail */
        get: operations["shared_detail_chat_shares__share_id__get"];
        put?: never;
        post?: never;
        /** Revoke */
        delete: operations["revoke_chat_shares__share_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/chat-shares": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Received Shares */
        get: operations["received_shares_chat_shares_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/tutor-settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Settings */
        get: operations["settings_tasks__task_id__tutor_settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Settings */
        patch: operations["update_settings_tasks__task_id__tutor_settings_patch"];
        trace?: never;
    };
    "/tasks/{task_id}/grading-guidance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Guidance */
        get: operations["guidance_tasks__task_id__grading_guidance_get"];
        put?: never;
        /** Save Guidance */
        post: operations["save_guidance_tasks__task_id__grading_guidance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/grading-guidance/{guidance_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Guidance Version */
        get: operations["guidance_version_tasks__task_id__grading_guidance__guidance_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/analytics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Analytics */
        get: operations["analytics_tasks__task_id__analytics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/analytics/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Reports */
        get: operations["reports_tasks__task_id__analytics_reports_get"];
        put?: never;
        /** Generate */
        post: operations["generate_tasks__task_id__analytics_reports_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/tasks/{task_id}/teams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Teams */
        get: operations["teams_tasks__task_id__teams_get"];
        put?: never;
        /** Create */
        post: operations["create_tasks__task_id__teams_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teams/{team_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_teams__team_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teams/{team_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** History */
        get: operations["history_teams__team_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teams/{team_id}/actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Act */
        post: operations["act_teams__team_id__actions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/team-invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Invitations */
        get: operations["invitations_team_invitations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/team-invitations/{invitation_id}/respond": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Respond */
        post: operations["respond_team_invitations__invitation_id__respond_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teams/{team_id}/repositories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_teams__team_id__repositories_get"];
        put?: never;
        /** Propose */
        post: operations["propose_teams__team_id__repositories_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/{repository_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_repositories__repository_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/{repository_id}/actions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Actions */
        post: operations["actions_repositories__repository_id__actions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/{repository_id}/commits": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Commits */
        get: operations["commits_repositories__repository_id__commits_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/{repository_id}/history": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** History */
        get: operations["history_repositories__repository_id__history_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/{repository_id}/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Snapshot */
        post: operations["snapshot_repositories__repository_id__snapshots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repository-snapshots/{snapshot_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Snapshot Detail */
        get: operations["snapshot_detail_repository_snapshots__snapshot_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repository-snapshots/{snapshot_id}/download": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Download */
        get: operations["download_repository_snapshots__snapshot_id__download_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AccountInfo */
        AccountInfo: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Email */
            email: string;
            /** Role */
            role: string;
            /** Student Number */
            student_number?: string | null;
            /** Cohort Year */
            cohort_year?: number | null;
            /** Major */
            major?: string | null;
            /** Department */
            department?: string | null;
            /** Github Username */
            github_username?: string | null;
            /** Profile Version */
            profile_version: number;
            /** Is Active */
            is_active: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AccountList */
        AccountList: {
            /** Items */
            items: components["schemas"]["AccountInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** AccountUpdate */
        AccountUpdate: {
            /** Expected Version */
            expected_version: number;
            /** Name */
            name?: string | null;
            /** Email */
            email?: string | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Role */
            role?: ("teaching_assistant" | "professor") | null;
            /** Student Number */
            student_number?: string | null;
            /** Cohort Year */
            cohort_year?: number | null;
            /** Major */
            major?: string | null;
            /** Department */
            department?: string | null;
            /** Github Username */
            github_username?: string | null;
        };
        /**
         * ApprovedRubricResponse
         * @description Student-facing grading expectations, never assessment output or staff drafts.
         */
        ApprovedRubricResponse: {
            /** Id */
            id: number;
            /** Version */
            version: number;
            /** Total */
            total: number;
            /** Criteria */
            criteria: components["schemas"]["RubricCriterionInput"][];
        };
        /** ArtifactResponse */
        ArtifactResponse: {
            /** File Id */
            file_id: number;
            /** File Name */
            file_name: string;
            /** File Type */
            file_type: string;
        };
        /** AuditInfo */
        AuditInfo: {
            /** Id */
            id: number;
            /** Actor Id */
            actor_id: number | null;
            /** Action */
            action: string;
            /** Target Type */
            target_type: string;
            /** Target Id */
            target_id: number;
            /** Fields */
            fields: string[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** AuditList */
        AuditList: {
            /** Items */
            items: components["schemas"]["AuditInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** Body_upload_files_upload_post */
        Body_upload_files_upload_post: {
            /** File */
            file: string;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "reference" | "submission" | "other";
            /** Task Id */
            task_id?: number | null;
            /** Submission Id */
            submission_id?: number | null;
        };
        /** ChatCreate */
        ChatCreate: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /**
             * Language
             * @default en
             * @enum {string}
             */
            language: "en" | "ar";
            /** Submission Id */
            submission_id?: number | null;
        };
        /** ChatInfo */
        ChatInfo: {
            /** Id */
            id: number;
            /** Task Id */
            task_id: number | null;
            /** Submission Id */
            submission_id: number | null;
            /** Title */
            title: string;
            /** Language */
            language: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** ChatList */
        ChatList: {
            /** Items */
            items: components["schemas"]["ChatInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** ChatSend */
        ChatSend: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Content */
            content: string;
            /**
             * Retry
             * @default false
             */
            retry: boolean;
        };
        /** ChatTurnInfo */
        ChatTurnInfo: {
            /** Id */
            id: number;
            /** Request Id */
            request_id: string;
            /** Content */
            content: string;
            /** Reply */
            reply: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "completed" | "failed";
            /** Error Code */
            error_code: string | null;
            /** Retryable */
            retryable: boolean;
            /** Is Mock */
            is_mock: boolean | null;
            context_info: components["schemas"]["TutorContextInfo"] | null;
            ai_metadata?: components["schemas"]["TutorMetadata"] | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** ChatTurnList */
        ChatTurnList: {
            /** Items */
            items: components["schemas"]["ChatTurnInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** CodeFindingResponse */
        CodeFindingResponse: {
            /** File Path */
            file_path: string;
            /** Line Number */
            line_number?: number | null;
            /** Severity */
            severity: string;
            /** Finding */
            finding: string;
        };
        /** CommitInfo */
        CommitInfo: {
            /** Id */
            id: number;
            /** Commit Hash */
            commit_hash: string;
            /** Author Name */
            author_name: string;
            /** Author Github Username */
            author_github_username: string;
            /** Message */
            message: string;
            /**
             * Committed At
             * Format: date-time
             */
            committed_at: string;
            /** Student Id */
            student_id: number | null;
            /** Attributed By */
            attributed_by: number | null;
            /** Attributed At */
            attributed_at: string | null;
        };
        /** CommitList */
        CommitList: {
            /** Items */
            items: components["schemas"]["CommitInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** CommonIssue */
        CommonIssue: {
            /** Title */
            title: string;
            /** Description */
            description: string;
            /**
             * Severity
             * @description info|warning|critical
             * @default warning
             */
            severity: string;
            /**
             * Affected Estimate
             * @description Human-readable estimate, e.g. 'many students' or '~40%'
             * @default
             */
            affected_estimate: string;
            /**
             * Evidence
             * @description What in the cohort data supports this
             * @default
             */
            evidence: string;
        };
        /** ConfirmGradeRequest */
        ConfirmGradeRequest: {
            /** Final Grade */
            final_grade: number;
        };
        /** CreateRubricRequest */
        CreateRubricRequest: {
            /** Criteria */
            criteria: components["schemas"]["RubricCriterionInput"][];
        };
        /** CreateSubmissionRequest */
        CreateSubmissionRequest: {
            /** Task Id */
            task_id: number;
            /**
             * Submission Text
             * @default
             */
            submission_text: string;
            /** Team Id */
            team_id?: number | null;
            /** File Id */
            file_id?: number | null;
            /** Repository Snapshot Id */
            repository_snapshot_id?: number | null;
        };
        /** CreateTaskRequest */
        CreateTaskRequest: {
            /**
             * Type
             * @enum {string}
             */
            type: "lab" | "assignment" | "project";
            /** Title */
            title: string;
            /** Description */
            description: string;
            /**
             * Due Date
             * Format: date-time
             */
            due_date: string;
            /** Target Cohort Year */
            target_cohort_year: number;
            /** Target Major */
            target_major?: string | null;
            /** Reference File Id */
            reference_file_id?: number | null;
            /** Scheduled Date */
            scheduled_date?: string | null;
            /** Allowed File Types */
            allowed_file_types?: string[];
            /**
             * Allow Late
             * @default false
             */
            allow_late: boolean;
            /**
             * Default Repo Provider
             * @default github
             */
            default_repo_provider: string | null;
            /**
             * Require Team
             * @default true
             */
            require_team: boolean;
        };
        /** CriterionEvaluationResponse */
        CriterionEvaluationResponse: {
            /** Criterion Name */
            criterion_name: string;
            /** Score Given */
            score_given: number;
            /** Max Points */
            max_points: number;
            /** Reasoning */
            reasoning: string;
        };
        /** CriterionStatistic */
        CriterionStatistic: {
            /** Criterion Id */
            criterion_id: number;
            /** Name */
            name: string;
            /** Label */
            label: string;
            /** Max Points */
            max_points: number;
            /** Sample Count */
            sample_count: number;
            /** Average Score */
            average_score: number | null;
            /** Low Score Count */
            low_score_count: number | null;
        };
        /** FileInfoResponse */
        FileInfoResponse: {
            /** File Id */
            file_id: number;
            /** File Name */
            file_name?: string | null;
            /** File Type */
            file_type: string;
            /** Purpose */
            purpose: string;
            /** Task Id */
            task_id?: number | null;
            /** Submission Id */
            submission_id?: number | null;
            /** Size Bytes */
            size_bytes?: number | null;
            /**
             * Uploaded At
             * Format: date-time
             */
            uploaded_at: string;
        };
        /** FileUploadResponse */
        FileUploadResponse: {
            /** File Id */
            file_id: number;
            /** File Name */
            file_name?: string | null;
            /** File Type */
            file_type: string;
            /** Purpose */
            purpose: string;
            /** Size Bytes */
            size_bytes?: number | null;
            /**
             * Uploaded At
             * Format: date-time
             */
            uploaded_at: string;
        };
        /** GuidanceCreate */
        GuidanceCreate: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Content */
            content: string;
        };
        /** GuidanceInfo */
        GuidanceInfo: {
            /** Id */
            id: number;
            /** Task Id */
            task_id: number;
            /** Version */
            version: number;
            /** Content */
            content: string;
            /** Created By */
            created_by: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** GuidanceList */
        GuidanceList: {
            /** Items */
            items: components["schemas"]["GuidanceInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** IdentityResponse */
        IdentityResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Email */
            email: string;
            /** Role */
            role: string;
            /** Student Number */
            student_number?: string | null;
            /** Cohort Year */
            cohort_year?: number | null;
            /** Major */
            major?: string | null;
            /** Department */
            department?: string | null;
            /** Github Username */
            github_username?: string | null;
            /** Profile Version */
            profile_version: number;
        };
        /** InvitationInfo */
        InvitationInfo: {
            /** Id */
            id: number;
            /** Team Id */
            team_id: number;
            /** Task Id */
            task_id: number;
            /** Team Name */
            team_name: string;
            /** Student Id */
            student_id: number;
            /** Name */
            name: string;
            /** Status */
            status: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** InvitationList */
        InvitationList: {
            /** Items */
            items: components["schemas"]["InvitationInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** InvitationReply */
        InvitationReply: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Expected Version */
            expected_version: number;
            /**
             * Decision
             * @enum {string}
             */
            decision: "accept" | "decline";
        };
        /** LegacyMessage */
        LegacyMessage: {
            /** Id */
            id: number;
            /**
             * Sender Type
             * @enum {string}
             */
            sender_type: "user" | "assistant";
            /** Content */
            content: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** LegacyMessages */
        LegacyMessages: {
            /** Items */
            items: components["schemas"]["LegacyMessage"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** LoginRequest */
        LoginRequest: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Password */
            password: string;
        };
        /** LoginResponse */
        LoginResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type: string;
            /** User Id */
            user_id: number;
            /** Role */
            role: string;
            /** Name */
            name: string;
        };
        /** ManifestFile */
        ManifestFile: {
            /** Path */
            path: string;
            /** Size */
            size: number;
            /** Sha256 */
            sha256: string;
            /** Included */
            included: boolean;
        };
        /** MetricGroup */
        MetricGroup: {
            /** Operation */
            operation: string;
            /** Provider */
            provider: string;
            /** Calls */
            calls: number;
            /** Errors */
            errors: number;
            /** Incomplete */
            incomplete: number;
            /** Average Latency Ms */
            average_latency_ms: number;
            /** Mock Calls */
            mock_calls: number;
            /** Unknown Mock Calls */
            unknown_mock_calls: number;
            /** Truncated Calls */
            truncated_calls: number;
            /** Unknown Truncation Calls */
            unknown_truncation_calls: number;
        };
        /** MetricsResponse */
        MetricsResponse: {
            /**
             * Since
             * Format: date-time
             */
            since: string;
            /** Groups */
            groups: components["schemas"]["MetricGroup"][];
        };
        /** Misconception */
        Misconception: {
            /** Concept */
            concept: string;
            /** Description */
            description: string;
            /**
             * Suggested Remediation
             * @default
             */
            suggested_remediation: string;
        };
        /** ProfileUpdate */
        ProfileUpdate: {
            /** Expected Version */
            expected_version: number;
            /** Name */
            name: string;
            /** Github Username */
            github_username?: string | null;
        };
        /** RefineRequest */
        RefineRequest: {
            /** Staff Feedback */
            staff_feedback: string;
        };
        /** RegisterRequest */
        RegisterRequest: {
            /** Name */
            name: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * @description Plain-text password — hashed before storage
             */
            password: string;
            /**
             * Role
             * @enum {string}
             */
            role: "professor" | "teaching_assistant" | "student";
            /**
             * Student Number
             * @description Required if role=student
             */
            student_number?: string | null;
            /**
             * Cohort Year
             * @description Required if role=student
             */
            cohort_year?: number | null;
            /**
             * Major
             * @description Required if role=student
             */
            major?: string | null;
            /** Github Username */
            github_username?: string | null;
            /**
             * Staff Role
             * @description professor | teaching_assistant — required if role=professor or teaching_assistant
             */
            staff_role?: string | null;
            /**
             * Department
             * @description Required if role=professor or teaching_assistant
             */
            department?: string | null;
        };
        /** RegisterResponse */
        RegisterResponse: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Email */
            email: string;
            /** Role */
            role: string;
            /**
             * Message
             * @default Account created successfully.
             */
            message: string;
        };
        /** ReportCreate */
        ReportCreate: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Rubric Id */
            rubric_id: number;
            /**
             * Language
             * @default en
             * @enum {string}
             */
            language: "en" | "ar";
        };
        /** RepositoryAction */
        RepositoryAction: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Expected Version */
            expected_version: number;
            /**
             * Action
             * @enum {string}
             */
            action: "approve" | "reject" | "sync" | "attribute";
            /** Commit Id */
            commit_id?: number | null;
            /** Student Id */
            student_id?: number | null;
        };
        /** RepositoryEventInfo */
        RepositoryEventInfo: {
            /** Id */
            id: number;
            /** Actor Id */
            actor_id: number;
            /** Action */
            action: string;
            /** Version */
            version: number;
            /** Details */
            details: {
                [key: string]: unknown;
            };
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** RepositoryEventList */
        RepositoryEventList: {
            /** Items */
            items: components["schemas"]["RepositoryEventInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** RepositoryInfo */
        RepositoryInfo: {
            /** Id */
            id: number;
            /** Task Id */
            task_id: number;
            /** Team Id */
            team_id: number;
            /** Repo Url */
            repo_url: string | null;
            /** Full Name */
            full_name: string | null;
            /** Status */
            status: string;
            /** Version */
            version: number;
            /** Approved Team Version */
            approved_team_version: number | null;
            /** Last Synced At */
            last_synced_at: string | null;
            /** Sync Error */
            sync_error: string | null;
            /** Partial History */
            partial_history: boolean;
            /** Is Fixture */
            is_fixture: boolean;
            /** Actions */
            actions: string[];
            /** Unavailable Reason */
            unavailable_reason: string | null;
        };
        /** RepositoryList */
        RepositoryList: {
            /** Items */
            items: components["schemas"]["RepositoryInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** RepositoryProposal */
        RepositoryProposal: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Repo Url */
            repo_url: string;
        };
        /** RepositoryReceipt */
        RepositoryReceipt: {
            /** Repository Id */
            repository_id: number;
            /** Version */
            version: number;
        };
        /** RosterMember */
        RosterMember: {
            /** Student Id */
            student_id: number;
            /** Name */
            name: string;
            /** Student Number */
            student_number: string;
            /** Accepted At */
            accepted_at: string | null;
        };
        /** RubricCreatedResponse */
        RubricCreatedResponse: {
            /** Rubric Id */
            rubric_id: number;
            /** Version */
            version: number;
            /** Status */
            status: string;
            /** Criteria */
            criteria: components["schemas"]["RubricCriterionInput"][];
        };
        /** RubricCriterionInput */
        RubricCriterionInput: {
            /** Name */
            name: string;
            /** Description */
            description?: string | null;
            /** Max Points */
            max_points: number;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** RubricGroup */
        RubricGroup: {
            /** Rubric Id */
            rubric_id: number;
            /** Rubric Version */
            rubric_version: number;
            /** Student Count */
            student_count: number;
            /** Eligible */
            eligible: boolean;
            /** Average Percentage */
            average_percentage: number | null;
            /** Minimum Percentage */
            minimum_percentage: number | null;
            /** Maximum Percentage */
            maximum_percentage: number | null;
            /** Below Half Count */
            below_half_count: number | null;
            /** Criteria */
            criteria: components["schemas"]["CriterionStatistic"][];
            /** Severity Counts */
            severity_counts: {
                [key: string]: number;
            } | null;
            /** Mock Assessment Count */
            mock_assessment_count: number;
            /** Unknown Provenance Count */
            unknown_provenance_count: number;
        };
        /** RubricListItem */
        RubricListItem: {
            /** Id */
            id: number;
            /** Version */
            version: number;
            /** Source */
            source: string;
            /** Status */
            status: string;
            /** Reviewed At */
            reviewed_at?: string | null;
            /** Criteria */
            criteria: components["schemas"]["RubricCriterionInput"][];
        };
        /** RubricUploadResponse */
        RubricUploadResponse: {
            /** Rubric Id */
            rubric_id: number;
            /** Version */
            version: number;
            /** Status */
            status: string;
        };
        /** ShareCreate */
        ShareCreate: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /**
             * Recipient Email
             * Format: email
             */
            recipient_email: string;
            /** Through Turn Id */
            through_turn_id: number;
            /** Preview Turn Ids */
            preview_turn_ids: number[];
        };
        /** ShareDetail */
        ShareDetail: {
            /** Id */
            id: number;
            /** Session Id */
            session_id: number;
            /** Task Id */
            task_id: number | null;
            /** Title */
            title: string;
            /** Student Name */
            student_name: string;
            /** Recipient Name */
            recipient_name: string;
            /** Through Turn Id */
            through_turn_id: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Revoked At */
            revoked_at: string | null;
            /** Snapshot */
            snapshot: components["schemas"]["SharedTurn"][];
        };
        /** ShareInfo */
        ShareInfo: {
            /** Id */
            id: number;
            /** Session Id */
            session_id: number;
            /** Task Id */
            task_id: number | null;
            /** Title */
            title: string;
            /** Student Name */
            student_name: string;
            /** Recipient Name */
            recipient_name: string;
            /** Through Turn Id */
            through_turn_id: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Revoked At */
            revoked_at: string | null;
        };
        /** ShareList */
        ShareList: {
            /** Items */
            items: components["schemas"]["ShareInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** SharedTurn */
        SharedTurn: {
            /** Id */
            id: number;
            /** Content */
            content: string;
            /** Reply */
            reply: string;
            /** Is Mock */
            is_mock: boolean | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** SnapshotInfo */
        SnapshotInfo: {
            /** Id */
            id: number;
            /** Repository Id */
            repository_id: number;
            /** Commit Sha */
            commit_sha: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            provenance: components["schemas"]["SnapshotProvenance"];
        };
        /** SnapshotProvenance */
        SnapshotProvenance: {
            /** Task Id */
            task_id: number;
            /** Team Id */
            team_id: number;
            /** Repository Id */
            repository_id: number;
            /** Repo Url */
            repo_url: string;
            /** Github Id */
            github_id: number;
            /** Commit Sha */
            commit_sha: string;
            /** Archive Sha256 */
            archive_sha256: string;
            /** Compressed Bytes */
            compressed_bytes: number;
            /**
             * Captured At
             * Format: date-time
             */
            captured_at: string;
            /** Team Version */
            team_version: number;
            /** Repository Version */
            repository_version: number;
            /** Is Fixture */
            is_fixture: boolean;
            /** Files */
            files: components["schemas"]["ManifestFile"][];
            /** Omitted Files */
            omitted_files: number;
            /** Attribution */
            attribution: {
                [key: string]: unknown;
            }[];
        };
        /** SnapshotRequest */
        SnapshotRequest: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Commit Sha */
            commit_sha: string;
        };
        /** StatusRequest */
        StatusRequest: {
            /** Status */
            status: string;
        };
        /** SubmissionConfirmedResponse */
        SubmissionConfirmedResponse: {
            /** Submission Id */
            submission_id: number;
            /** Status */
            status: string;
            /** Final Grade */
            final_grade: number;
            /** Confirmed By */
            confirmed_by?: number | null;
            /** Confirmed At */
            confirmed_at?: string | null;
        };
        /** SubmissionCreatedResponse */
        SubmissionCreatedResponse: {
            /** Submission Id */
            submission_id: number;
            /** Task Id */
            task_id: number;
            /** Attempt Number */
            attempt_number: number;
            /** Status */
            status: string;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
        };
        /** SubmissionDetailResponse */
        SubmissionDetailResponse: {
            repository_snapshot?: components["schemas"]["SnapshotInfo"] | null;
            team_snapshot?: components["schemas"]["TeamSnapshot"] | null;
            /** Grading Guidance Id */
            grading_guidance_id?: number | null;
            /** Grading Guidance Version */
            grading_guidance_version?: number | null;
            /** Id */
            id: number;
            /** Task Id */
            task_id: number;
            /** Student Id */
            student_id: number;
            /** Team Id */
            team_id?: number | null;
            /** File Id */
            file_id?: number | null;
            /** Submission Text */
            submission_text?: string | null;
            /** Attempt Number */
            attempt_number: number;
            /** Is Latest */
            is_latest: boolean;
            /** Status */
            status: string;
            /** Ai Suggested Grade */
            ai_suggested_grade?: number | null;
            /** Final Grade */
            final_grade?: number | null;
            /** Feedback */
            feedback?: string | null;
            /** Confirmed By */
            confirmed_by?: number | null;
            /** Confirmed At */
            confirmed_at?: string | null;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /** Rubric Id */
            rubric_id: number;
            /** Rubric Version */
            rubric_version: number;
            /** Total Possible Grade */
            total_possible_grade: number;
            /** Rubric Criteria */
            rubric_criteria?: components["schemas"]["RubricCriterionInput"][];
            /** Artifacts */
            artifacts?: components["schemas"]["ArtifactResponse"][];
            /** Criterion Evaluations */
            criterion_evaluations?: components["schemas"]["CriterionEvaluationResponse"][] | null;
            /** Code Reviews */
            code_reviews?: components["schemas"]["CodeFindingResponse"][] | null;
            /** Ai Warnings */
            ai_warnings?: string[] | null;
            /** Is Mock */
            is_mock?: boolean | null;
        };
        /** SubmissionEligibility */
        SubmissionEligibility: {
            /** Team Id */
            team_id?: number | null;
            /** Allowed */
            allowed: boolean;
            /** Reason Code */
            reason_code?: string | null;
            /** Rubric Ready */
            rubric_ready: boolean;
            /** Rubric Total */
            rubric_total?: number | null;
        };
        /** SubmissionGradedResponse */
        SubmissionGradedResponse: {
            /** Submission Id */
            submission_id: number;
            /** Status */
            status: string;
            /** Ai Suggested Grade */
            ai_suggested_grade?: number | null;
            /** Feedback */
            feedback?: string | null;
        };
        /** SubmissionListItemResponse */
        SubmissionListItemResponse: {
            /** Id */
            id: number;
            /** Attempt Number */
            attempt_number: number;
            /** Is Latest */
            is_latest: boolean;
            /** Status */
            status: string;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /** Ai Suggested Grade */
            ai_suggested_grade?: number | null;
            /** Final Grade */
            final_grade?: number | null;
            /** Feedback */
            feedback?: string | null;
            /** Total Possible Grade */
            total_possible_grade?: number | null;
        };
        /** SubmissionQueueItem */
        SubmissionQueueItem: {
            /** Id */
            id: number;
            /** Attempt Number */
            attempt_number: number;
            /** Is Latest */
            is_latest: boolean;
            /** Status */
            status: string;
            /**
             * Submitted At
             * Format: date-time
             */
            submitted_at: string;
            /** Ai Suggested Grade */
            ai_suggested_grade?: number | null;
            /** Final Grade */
            final_grade?: number | null;
            /** Feedback */
            feedback?: string | null;
            /** Total Possible Grade */
            total_possible_grade?: number | null;
            /** Student Id */
            student_id: number;
            /** Student Name */
            student_name: string;
            /** Student Number */
            student_number: string;
        };
        /**
         * SubmissionStatus
         * @enum {string}
         */
        SubmissionStatus: "pending" | "ai_graded" | "staff_confirmed";
        /** TaskAnalytics */
        TaskAnalytics: {
            /** Task Id */
            task_id: number;
            /** Minimum Group Size */
            minimum_group_size: number;
            /** Released Count */
            released_count: number;
            /** Excluded Count */
            excluded_count: number;
            /** Input Fingerprint */
            input_fingerprint: string;
            /** Groups */
            groups: components["schemas"]["RubricGroup"][];
        };
        /** TaskAssignmentDetailsResponse */
        TaskAssignmentDetailsResponse: {
            /** Allowed File Types */
            allowed_file_types?: string[] | null;
            /**
             * Allow Late
             * @default false
             */
            allow_late: boolean;
        };
        /** TaskCreatedResponse */
        TaskCreatedResponse: {
            /** Id */
            id: number;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /**
             * Due Date
             * Format: date-time
             */
            due_date: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** TaskDetailResponse */
        TaskDetailResponse: {
            /** Id */
            id: number;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Description */
            description: string;
            /**
             * Due Date
             * Format: date-time
             */
            due_date: string;
            /** Target Cohort Year */
            target_cohort_year: number;
            /** Target Major */
            target_major?: string | null;
            /** Reference File Id */
            reference_file_id?: number | null;
            latest_submission?: components["schemas"]["SubmissionListItemResponse"] | null;
            /** Review Counts */
            review_counts?: {
                [key: string]: number;
            } | null;
            /** Created By */
            created_by: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            submission_eligibility: components["schemas"]["SubmissionEligibility"];
            accepted_rubric?: components["schemas"]["ApprovedRubricResponse"] | null;
            lab_details?: components["schemas"]["TaskLabDetailsResponse"] | null;
            assignment_details?: components["schemas"]["TaskAssignmentDetailsResponse"] | null;
            project_details?: components["schemas"]["TaskProjectDetailsResponse"] | null;
        };
        /** TaskLabDetailsResponse */
        TaskLabDetailsResponse: {
            /** Scheduled Date */
            scheduled_date?: string | null;
        };
        /** TaskListItemResponse */
        TaskListItemResponse: {
            /** Id */
            id: number;
            /** Type */
            type: string;
            /** Title */
            title: string;
            /** Description */
            description: string;
            /**
             * Due Date
             * Format: date-time
             */
            due_date: string;
            /** Target Cohort Year */
            target_cohort_year: number;
            /** Target Major */
            target_major?: string | null;
            /** Reference File Id */
            reference_file_id?: number | null;
            latest_submission?: components["schemas"]["SubmissionListItemResponse"] | null;
            /** Review Counts */
            review_counts?: {
                [key: string]: number;
            } | null;
        };
        /** TaskProjectDetailsResponse */
        TaskProjectDetailsResponse: {
            /** Default Repo Provider */
            default_repo_provider?: string | null;
            /**
             * Require Team
             * @default true
             */
            require_team: boolean;
        };
        /** TeachingReportInfo */
        TeachingReportInfo: {
            /** Id */
            id: number;
            /** Task Id */
            task_id: number;
            /** Rubric Id */
            rubric_id: number;
            /** Rubric Version */
            rubric_version: number;
            /** Language */
            language: string;
            /** Input Fingerprint */
            input_fingerprint: string;
            input_snapshot: components["schemas"]["RubricGroup"];
            result: components["schemas"]["TeachingSuggestions"];
            /** Is Mock */
            is_mock: boolean;
            ai_metadata: components["schemas"]["TutorMetadata"] | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Stale */
            stale: boolean;
        };
        /** TeachingReportList */
        TeachingReportList: {
            /** Items */
            items: components["schemas"]["TeachingReportInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** TeachingSuggestions */
        TeachingSuggestions: {
            /** Summary */
            summary: string;
            /** Common Issues */
            common_issues?: components["schemas"]["CommonIssue"][];
            /** Misconceptions */
            misconceptions?: components["schemas"]["Misconception"][];
            /** Teaching Focus */
            teaching_focus?: string[];
            /** Warnings */
            warnings?: string[];
        };
        /** TeamAction */
        TeamAction: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Expected Version */
            expected_version: number;
            /**
             * Action
             * @enum {string}
             */
            action: "invite" | "remove" | "cancel_invitation" | "leave" | "archive" | "request_approval" | "approve" | "reject";
            /** Student Number */
            student_number?: string | null;
            /** Student Id */
            student_id?: number | null;
            /** Invitation Id */
            invitation_id?: number | null;
        };
        /** TeamCreate */
        TeamCreate: {
            /**
             * Request Id
             * Format: uuid
             */
            request_id: string;
            /** Name */
            name: string;
        };
        /** TeamEventInfo */
        TeamEventInfo: {
            /** Id */
            id: number;
            /** Action */
            action: string;
            /** Version */
            version: number;
            roster: components["schemas"]["TeamSnapshot"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
        };
        /** TeamEventList */
        TeamEventList: {
            /** Items */
            items: components["schemas"]["TeamEventInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** TeamInfo */
        TeamInfo: {
            /** Id */
            id: number;
            /** Task Id */
            task_id: number;
            /** Name */
            name: string;
            /** Created By */
            created_by: number | null;
            /** Status */
            status: string;
            /** Version */
            version: number;
            /** Locked At */
            locked_at: string | null;
            /** Members */
            members: components["schemas"]["RosterMember"][];
            /** Invitations */
            invitations: components["schemas"]["InvitationInfo"][];
            /** Actions */
            actions: string[];
            /** Unavailable Reason */
            unavailable_reason: string | null;
        };
        /** TeamList */
        TeamList: {
            /** Items */
            items: components["schemas"]["TeamInfo"][];
            /** Next Cursor */
            next_cursor: number | null;
        };
        /** TeamMutationResult */
        TeamMutationResult: {
            /** Team Id */
            team_id: number;
            /** Version */
            version: number;
        };
        /** TeamSnapshot */
        TeamSnapshot: {
            /** Team Id */
            team_id: number;
            /** Name */
            name: string;
            /** Version */
            version: number;
            /** Members */
            members: components["schemas"]["RosterMember"][];
        };
        /** TutorContextInfo */
        TutorContextInfo: {
            /** Task Id */
            task_id: number;
            /** Reference File Id */
            reference_file_id?: number | null;
            /** Rubric Version */
            rubric_version?: number | null;
            /** Submission Id */
            submission_id?: number | null;
            /**
             * Released Feedback
             * @default false
             */
            released_feedback: boolean;
            /**
             * Truncated
             * @default false
             */
            truncated: boolean;
            /** Lab Mode */
            lab_mode?: string | null;
        };
        /** TutorMetadata */
        TutorMetadata: {
            /** Provider */
            provider?: string | null;
            /** Model Used */
            model_used?: string | null;
            /** Prompt Version */
            prompt_version?: string | null;
            /** Ai Engine Version */
            ai_engine_version?: string | null;
            /** Latency Ms */
            latency_ms: number;
            /**
             * Output Sanitized
             * @default false
             */
            output_sanitized: boolean;
        };
        /** TutorSettings */
        TutorSettings: {
            /**
             * Lab Mode
             * @default experiment
             * @enum {string}
             */
            lab_mode: "experiment" | "coding";
        };
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    me_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IdentityResponse"];
                };
            };
        };
    };
    update_me_auth_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfileUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["IdentityResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RegisterRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RegisterResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LoginResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    users_admin_users_get: {
        parameters: {
            query?: {
                q?: string;
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    user_detail_admin_users__user_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    correct_admin_users__user_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AccountUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccountInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    audit_admin_audit_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuditList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    metrics_admin_ai_metrics_get: {
        parameters: {
            query?: {
                days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MetricsResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_all_tasks__get: {
        parameters: {
            query?: {
                cohort_year?: number | null;
                major?: string | null;
                task_type?: string | null;
                /** @description Filter for tasks whose due date has not passed */
                filter_due_tasks?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TaskListItemResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_tasks__post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateTaskRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TaskCreatedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    task_submissions_tasks__task_id__submissions_get: {
        parameters: {
            query?: {
                latest_only?: boolean;
                status?: components["schemas"]["SubmissionStatus"] | null;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionQueueItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_one_tasks__task_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TaskDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_tasks__task_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_files_upload_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_files_upload_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FileUploadResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_file_info_files__file_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                file_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FileInfoResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_file_files__file_id__download_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                file_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_submissions__post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateSubmissionRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionCreatedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_submissions_submissions_my__task_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionListItemResponse"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    grade_submissions__submission_id__grade_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionGradedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    confirm_submissions__submission_id__confirm_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConfirmGradeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionConfirmedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_one_submissions__submission_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                submission_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionDetailResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    suggest_tasks__task_id__rubrics_suggest_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RubricUploadResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refine_tasks__task_id__rubrics_refine_post: {
        parameters: {
            query?: {
                rubric_id?: number | null;
                version?: number | null;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefineRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RubricUploadResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_tasks__task_id__rubrics_create_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreateRubricRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RubricCreatedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_status_tasks__task_id__rubrics_status_patch: {
        parameters: {
            query?: {
                rubric_id?: number | null;
                version?: number | null;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StatusRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RubricUploadResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_all_rubrics_tasks__task_id__rubrics_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RubricListItem"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sessions_tasks__task_id__chat_sessions_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_tasks__task_id__chat_sessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChatCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_chat_sessions__session_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    messages_chat_sessions__session_id__messages_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatTurnList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    send_chat_sessions__session_id__messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChatSend"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChatTurnInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    legacy_chat_sessions__session_id__legacy_messages_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LegacyMessages"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_chat_sessions__session_id__share_preview_get: {
        parameters: {
            query: {
                through_turn_id: number;
            };
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SharedTurn"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    owner_shares_chat_sessions__session_id__shares_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShareList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    share_chat_sessions__session_id__shares_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ShareCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShareInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    shared_detail_chat_shares__share_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                share_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShareDetail"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    revoke_chat_shares__share_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                share_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    received_shares_chat_shares_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ShareList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    settings_tasks__task_id__tutor_settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TutorSettings"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_settings_tasks__task_id__tutor_settings_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TutorSettings"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TutorSettings"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    guidance_tasks__task_id__grading_guidance_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidanceList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_guidance_tasks__task_id__grading_guidance_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuidanceCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidanceInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    guidance_version_tasks__task_id__grading_guidance__guidance_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
                guidance_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuidanceInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    analytics_tasks__task_id__analytics_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TaskAnalytics"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reports_tasks__task_id__analytics_reports_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeachingReportList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_tasks__task_id__analytics_reports_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReportCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeachingReportInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    teams_tasks__task_id__teams_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
                status?: string | null;
            };
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_tasks__task_id__teams_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                task_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TeamCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_teams__team_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                team_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    history_teams__team_id__history_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                team_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamEventList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    act_teams__team_id__actions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                team_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TeamAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamMutationResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    invitations_team_invitations_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    respond_team_invitations__invitation_id__respond_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invitation_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InvitationReply"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TeamMutationResult"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_teams__team_id__repositories_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                team_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    propose_teams__team_id__repositories_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                team_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepositoryProposal"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_repositories__repository_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repository_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    actions_repositories__repository_id__actions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repository_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepositoryAction"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryReceipt"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    commits_repositories__repository_id__commits_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                repository_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CommitList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    history_repositories__repository_id__history_get: {
        parameters: {
            query?: {
                before?: number | null;
                limit?: number;
            };
            header?: never;
            path: {
                repository_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryEventList"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    snapshot_repositories__repository_id__snapshots_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                repository_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SnapshotRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    snapshot_detail_repository_snapshots__snapshot_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                snapshot_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_repository_snapshots__snapshot_id__download_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                snapshot_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
}
