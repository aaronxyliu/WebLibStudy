import re

class StandardVersion:
    def __init__(self, version_str: str):
        version_str = str(version_str)

        self.raw_str = self.major_version = self.minor_version = self.patch_version = self.suffix = None

        self.raw_str = version_str
        self.major_version = self.minor_version = self.patch_version = self.suffix = None
        res1 = re.search('[0-9]+', version_str)
        if res1:
            self.major_version = int(res1.group())
            version_str = version_str[res1.span()[1]:]

            res2 = re.search('[0-9]+', version_str)
            if res2:
                self.minor_version = int(res2.group())   
                version_str = version_str[res2.span()[1]:]

                res3 = re.search('[0-9]+', version_str)
                if res3:
                    self.patch_version = int(res3.group())   
                    version_str = version_str[res3.span()[1]:]
        self.suffix = version_str
        
    def __eq__(self, x: object) -> bool:
        # Equal overloading
        if self.raw_str and x.raw_str and self.raw_str == x.raw_str:
            return True
        if self.major_version == None or self.major_version == None:
            return False
        if self.major_version != x.major_version:
            return False
        if self.minor_version  == None or x.minor_version  == None:
            return True
        if self.minor_version != x.minor_version:
            return False
        if self.patch_version == None or x.patch_version == None:
            return True
        if self.patch_version != x.patch_version:
            return False
        return True
        # if not self.suffix or not x.suffix:
        #     return True
        # if self.suffix != x.suffix:
        #     return False

    def __lt__(self, x: object) -> bool:
        # Less than overloading
        if self.major_version != None and x.major_version == None:
            return False
        elif self.major_version == None and x.major_version != None:
            return True
        elif self.major_version != None and x.major_version != None:
            if self.major_version != x.major_version:
                return self.major_version < x.major_version
            else:
                if self.minor_version != None and x.minor_version == None:
                    return False
                elif self.minor_version == None and x.minor_version != None:
                    return True
                elif self.minor_version != None and x.minor_version != None:
                    if self.minor_version != x.minor_version:
                        return self.minor_version < x.minor_version
                    else:
                        if self.patch_version != None and x.patch_version == None:
                            return False
                        elif self.patch_version == None and x.patch_version != None:
                            return True
                        elif self.patch_version != None and x.patch_version != None:
                            if self.patch_version != x.patch_version:
                                return self.patch_version < x.patch_version
        return self.suffix < x.suffix
        
    def __str__(self) -> str:
        print_content = f'''Major version: {self.major_version}\n\
Minor version: {self.minor_version}\n\
Patch version: {self.patch_version}\n\
Suffix: {self.suffix}
        '''
        return print_content
    
    def onlySuffix(self) -> bool:
        if self.major_version == None:
            return True
        return False


# a = StandardVersion('v0.2.3')
# b = StandardVersion('0.2.3')
# print(a)
# print(b)
# print(a<b)
# print(b<a)
# print(a==b)