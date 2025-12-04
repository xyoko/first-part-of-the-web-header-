2
    
        async function approveRecipe(id){
            if(!confirm('Approve?')) return;
            const res = await fetch(`/api/recipes/${id}/approve`, { method:'POST' });
            if (res.ok) location.reload();
            else alert('Failed');
        }
        async function rejectRecipe(id){
            if(!confirm('Reject?')) return;
            const res = await fetch(`/api/recipes/${id}/reject`, { method:'POST' });
            if (res.ok) location.reload();
            else alert('Failed');
        }
        async function moderateComment(commentId, action) {
            if (!confirm('Are you sure?')) return;
            let url = `/api/comments/${commentId}/remove`;
            if (action === 'restore') url = `/api/comments/${commentId}/restore`;
            const res = await fetch(url, { method: 'POST' });
            if (res.ok) location.reload();
            else alert('Failed');
        }
