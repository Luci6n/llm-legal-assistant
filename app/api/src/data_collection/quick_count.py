import os
import json
from pathlib import Path
from collections import defaultdict

def analyze_duplicate_files(base_dir="data/raw/legal_cases"):
    """Analyze and display duplicate file statistics"""
    
    download_dir = Path(base_dir)
    metadata_dir = download_dir / "metadata"
    
    if not download_dir.exists():
        print(f"❌ Directory not found: {download_dir}")
        return None
    
    # Get all PDF files
    pdf_files = list(download_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in the directory")
        return None
    
    # Track base names and their versions
    file_groups = defaultdict(list)
    
    for pdf_file in pdf_files:
        filename = pdf_file.stem  # filename without extension
        
        # Extract base name by removing version suffix (_1, _2, etc.)
        if '_' in filename:
            parts = filename.split('_')
            # Check if last part is a number (version suffix)
            if parts[-1].isdigit():
                base_name = '_'.join(parts[:-1])
                version_num = int(parts[-1])
            else:
                base_name = filename
                version_num = 0  # Original file
        else:
            base_name = filename
            version_num = 0  # Original file
        
        file_groups[base_name].append({
            'filename': pdf_file.name,
            'version': version_num,
            'path': pdf_file
        })
    
    # Sort versions for each base name
    for base_name in file_groups:
        file_groups[base_name].sort(key=lambda x: x['version'])
    
    # Separate duplicates from unique files
    duplicates = {name: files for name, files in file_groups.items() if len(files) > 1}
    unique_files = {name: files for name, files in file_groups.items() if len(files) == 1}
    
    # Display results
    print("\n" + "="*80)
    print("🔍 DUPLICATE FILE ANALYSIS")
    print("="*80)
    print(f"📁 Directory: {download_dir.absolute()}")
    print(f"📄 Total PDF files: {len(pdf_files)}")
    print(f"🔖 Total unique case names: {len(file_groups)}")
    print(f"✅ Cases with single file: {len(unique_files)}")
    print(f"🔄 Cases with duplicates: {len(duplicates)}")
    
    if duplicates:
        total_duplicate_files = sum(len(files) - 1 for files in duplicates.values())
        print(f"📋 Total duplicate files: {total_duplicate_files}")
        
        print("\n" + "="*80)
        print("🔄 DUPLICATE FILE STATISTICS:")
        print("="*80)
        
        # Sort duplicates by number of versions (most duplicates first)
        sorted_duplicates = sorted(duplicates.items(), 
                                 key=lambda x: len(x[1]), 
                                 reverse=True)
        
        for base_name, files in sorted_duplicates:
            print(f"\n📝 {base_name}: {len(files)} versions")
            for file_info in files:
                size_mb = file_info['path'].stat().st_size / (1024 * 1024)
                if file_info['version'] == 0:
                    print(f"   • {file_info['filename']} (original) - {size_mb:.2f} MB")
                else:
                    print(f"   • {file_info['filename']} (version {file_info['version']}) - {size_mb:.2f} MB")
        
        print("\n" + "="*80)
        
    else:
        print("\n✅ No duplicate files found!")
    
    return {
        'total_files': len(pdf_files),
        'unique_cases': len(file_groups),
        'duplicate_cases': len(duplicates),
        'duplicates': duplicates
    }

def show_duplicate_summary(base_dir="data/raw/legal_cases"):
    """Show a quick summary of duplicates (like in your scraper)"""
    
    result = analyze_duplicate_files(base_dir)
    
    if result and result['duplicates']:
        print("\n🔄 Duplicate file statistics:")
        for base_name, files in result['duplicates'].items():
            print(f"   {base_name}: {len(files)} versions")

def find_specific_duplicates(search_term, base_dir="data/raw/legal_cases"):
    """Find duplicates containing a specific search term"""
    
    download_dir = Path(base_dir)
    if not download_dir.exists():
        print(f"❌ Directory not found: {download_dir}")
        return
    
    pdf_files = list(download_dir.glob("*.pdf"))
    file_groups = defaultdict(list)
    
    # Group files by base name
    for pdf_file in pdf_files:
        filename = pdf_file.stem
        if '_' in filename and filename.split('_')[-1].isdigit():
            base_name = '_'.join(filename.split('_')[:-1])
        else:
            base_name = filename
        file_groups[base_name].append(pdf_file.name)
    
    # Find matches
    matches = {name: files for name, files in file_groups.items() 
              if search_term.lower() in name.lower() and len(files) > 1}
    
    if matches:
        print(f"\n🔍 Duplicates containing '{search_term}':")
        for base_name, files in matches.items():
            print(f"   {base_name}: {len(files)} versions")
            for file in files:
                print(f"     • {file}")
    else:
        print(f"❌ No duplicates found containing '{search_term}'")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            show_duplicate_summary()
        elif command == "search" and len(sys.argv) > 2:
            find_specific_duplicates(sys.argv[2])
        else:
            print("Usage:")
            print("  python check_duplicates.py          # Full analysis")
            print("  python check_duplicates.py summary  # Quick summary")
            print("  python check_duplicates.py search <term>  # Search duplicates")
            print("  python check_duplicates.py remove   # Remove duplicates")
    else:
        # Default: full analysis
        analyze_duplicate_files()