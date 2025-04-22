import React, { useEffect, useState } from 'react';
import Image from 'next/image'

const Footer = () => {
  const currentYear = new Date().getFullYear();
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Detect dark mode by checking the 'dark' class on html element
  useEffect(() => {
    // Check initial state
    const isDark = document.documentElement.classList.contains('dark');
    setIsDarkMode(isDark);
    
    // Set up a MutationObserver to detect changes to the classList of the html element
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          const isDark = document.documentElement.classList.contains('dark');
          setIsDarkMode(isDark);
        }
      });
    });
    
    // Start observing
    observer.observe(document.documentElement, { attributes: true });
    
    // Clean up
    return () => {
      observer.disconnect();
    };
  }, []);
  
  return (
    <footer className="bg-accent/100 backdrop-blur-sm border-t border-border mt-12 py-6 w-full">
      <div className="max-w-4xl mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          {/* Logo Section */}
          <div className="flex items-center gap-3">
            <Image src="/logo.png" width={40} height={40} alt="" />
            <p className="text-4xl font-ubuntu bg-gradient-to-r from-primary to-primary/80 bg-clip-text text-transparent">
              DORI
            </p>
          </div>
          
          {/* Credits and Sponsorship */}
          <div className="text-center md:text-right">
            <p className="text-sm text-muted-foreground">
              Built by a Clemson University Capstone Team
            </p>
            <div className="flex items-center justify-center md:justify-end gap-2 mt-2">
              <span className="text-xs text-muted-foreground">Powered by and sponsored with an academic grant from</span>
              <a 
                href="https://build.nvidia.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="opacity-80 hover:opacity-100 transition-opacity"
              >
                {/* Conditional rendering based on theme */}
                {isDarkMode ? (
                  <Image 
                    src="/Nvidia-Dark.png" 
                    width={160} 
                    height={48} 
                    alt="NVIDIA Logo" 
                  />
                ) : (
                  <Image 
                    src="/Nvidia-Light.png" 
                    width={120} 
                    height={36} 
                    alt="NVIDIA Logo" 
                  />
                )}
              </a>
            </div>
          </div>
        </div>
        
        {/* GitHub Link and Copyright */}
        <div className="mt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex gap-4 text-sm text-muted-foreground">
            <a 
              href="https://github.com/Clemson-Capstone/s25-nvidia" 
              target="_blank" 
              rel="noopener noreferrer"
              className="hover:text-primary transition-colors flex items-center gap-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                <path d="M9 18c-4.51 2-5-2-7-2"></path>
              </svg>
              GitHub
            </a>
          </div>
          <div className="text-xs text-muted-foreground">
            © {currentYear} Clemson Capstone Team. Open source project.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;