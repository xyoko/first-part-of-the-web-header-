// ===========================
// Mobile Menu Toggle
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const nav = document.querySelector('.nav');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            nav.style.display = nav.style.display === 'flex' ? 'none' : 'flex';
            
            // If showing menu, position it absolutely below header
            if (nav.style.display === 'flex') {
                nav.style.position = 'absolute';
                nav.style.top = '100%';
                nav.style.left = '0';
                nav.style.right = '0';
                nav.style.backgroundColor = 'var(--color-card)';
                nav.style.flexDirection = 'column';
                nav.style.padding = '1rem';
                nav.style.borderTop = '1px solid var(--color-border)';
                nav.style.boxShadow = 'var(--shadow-md)';
            }
        });
    }
    
    // ===========================
    // Smooth Scrolling for Anchor Links
    // ===========================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId !== '#' && targetId !== '') {
                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // ===========================
    // Ingredient Checkbox Functionality
    // ===========================
    const ingredientCheckboxes = document.querySelectorAll('.ingredient-checkbox');
    
    ingredientCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (this.checked) {
                label.style.textDecoration = 'line-through';
                label.style.color = 'var(--color-muted-foreground)';
            } else {
                label.style.textDecoration = 'none';
                label.style.color = 'var(--color-foreground)';
            }
        });
    });
    
    // ===========================
    // Search Bar Functionality ( VERY VERYBasic)
    // ===========================
    const searchInput = document.querySelector('.search-input');
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const searchTerm = this.value.trim();
                if (searchTerm) {
                    alert(`Searching for: ${searchTerm}`);
                    // In a real application, this would navigate to a search results page
                    // or filter the recipes on the current page
                }
            }
        });
    }
    
    // ===========================
    // Recipe Card Click Analytics (Optional)
    // ===========================
    const recipeCards = document.querySelectorAll('.recipe-card');
    
    recipeCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Only log if not clicking the button directly
            if (!e.target.classList.contains('btn')) {
                const recipeName = this.querySelector('.recipe-name')?.textContent;
                console.log(`Recipe viewed: ${recipeName}`);
                // Here you could send analytics data to a tracking service
            }
        });
    });
    
    // ===========================
    // Save Recipe Button (Recipe Detail Page)
    // ===========================
    const saveButtons = document.querySelectorAll('.btn-primary');
    
    saveButtons.forEach(button => {
        if (button.textContent.includes('Save Recipe')) {
            button.addEventListener('click', function() {
                const currentText = this.textContent;
                if (currentText.includes('Save')) {
                    this.textContent = '✓ Saved';
                    this.style.backgroundColor = 'var(--color-secondary)';
                    
                    // Revert after 2 seconds
                    setTimeout(() => {
                        this.textContent = 'Save Recipe';
                        this.style.backgroundColor = 'var(--color-primary)';
                    }, 2000);
                }
            });
        }
    });
    
    // ===========================
    // Share Button Functionality
    // ===========================
    const shareButtons = document.querySelectorAll('.btn-outline');
    
    shareButtons.forEach(button => {
        if (button.textContent.includes('Share')) {
            button.addEventListener('click', async function() {
                const pageTitle = document.title;
                const pageUrl = window.location.href;
                
                // Check if Web Share API is available
                if (navigator.share) {
                    try {
                        await navigator.share({
                            title: pageTitle,
                            url: pageUrl
                        });
                        console.log('Recipe shared successfully');
                    } catch (err) {
                        console.log('Error sharing:', err);
                    }
                } else {
                    // Fallback: Copy to clipboard
                    try {
                        await navigator.clipboard.writeText(pageUrl);
                        alert('Link copied to clipboard!');
                    } catch (err) {
                        alert('Unable to share. Please copy the URL manually.');
                    }
                }
            });
        }
    });
    
    // ===========================
    // Add scroll effect to header
    // ===========================
    let lastScroll = 0;
    const header = document.querySelector('.header');
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            header.style.boxShadow = 'var(--shadow-lg)';
        } else {
            header.style.boxShadow = 'var(--shadow-sm)';
        }
        
        lastScroll = currentScroll;
    });
});
