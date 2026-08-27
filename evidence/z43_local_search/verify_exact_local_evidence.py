#!/usr/bin/env python3
"""Verify the committed local-repair table and optional transient artifacts."""

import argparse
import hashlib
from pathlib import Path


CASES = {
    1: ("df22cc5d6c8bc49554e69cf42fa430a91a56b55881fa9a55bd8ae582f422717a", "fd51d4d87debef5ce6947910cfbc9285326ff23256bce6e64f94f28e89d1542d", "f1287919404ea4b941bb9e10ce23f779993f760e2466b38cf9e12a5ba5a25fdb"),
    2: ("7080b02113c546700ab60caacfa485d1703ad0ea5d7d7fd16cf6d2b044f87104", "149ff4cbbdf8815b4ba5118559c8fad0511996208fb6ec1f4f7be472c32993a8", "d179f390107cc3481f171602d3b2d6f0f682efbbe46b402ae3140c48e7575741"),
    3: ("203b5ec62f400f4386eacecbfdd9ba36ca32d030ec79124652b9095da0b93390", "e33ec9fc2c6cc82d8b99b573c0dd706dbdafc08937dceb47cd697ce086422e55", "2d59985d1661d48037a496fb796d6e81eac8d294659b6ba6c7348249c84b3daa"),
    4: ("126cac8aadfd5687a731e783e07c017fe278e574a39b39287ba0b45a3305f228", "3465c7865d4e83b694ce6e1d819a0c3a67e7e432439d88f627b09b0c2ee17413", "fd307160fbaf224c46838285658faf5b77534e093486bb40eb012d905abea952"),
    5: ("d569f0663f0ed3ad4ceb1d38618f0c9546eb86c0bbfaa56fa28ec403ec982d5a", "045a78405dfbab1a1a21e1ab0b34200a434bd50e043769fdf97a736f77e6244c", "24cf772f523e21959ece1e1639f024aaa18d9654b6ab5d48b9e6db792d7c1c46"),
    6: ("606451f58561c5ae4d55330539e2e6c3cf1eeb7f35a556445d3f754bdbd6a540", "3d8f975658a82d633ac4c78de714c22ad3e05d9dc91317e53a3022549a11c539", "b9e3ec2f299ace5a70d4c948a415b7308d66d90b00204304df174010eef97779"),
    7: ("e9022858ae3b3eeb39eb76888fa5980b845ac284ddd363f20d6744852b62f784", "b80373400fdd8821be31e9994c914f1ac3752fa162b97d9f8c2db4138e135eaf", "7004311fb1a204efda45eeedefbb7b158cea0122b8b30e3049604c72f162069d"),
    8: ("9fac70649980dd0f757a879bfadd6fa5f68dff0e740d3f8d5e0c5cb2083a3c73", "e43a0282f1d34f74e2486100d41adc9e3e6edce5322de9b6691fdf796552f12d", "a9b933d18485596e0c93fafbe759061c712e2cb71eb048ecacaf5a1783ea7345"),
    9: ("ffc36a6a4ddec53a415d38a77a9f7bd4d231d117fe1f6d86994648369f2c6f62", "ee0202de75e58025f304f52e62e085e9eca2a6713b4ce8bfabdb95931d05a650", "861456b7a876d2c436ea14993aa833c65b6d5a97112d44d224f08bacae788bb8"),
    10: ("7eac77809d7b935f944fb1b702070cdc7ee6039a5f55674f955f275c2c5c3f12", "0d49d765d26559f30520e76f8145e1f13413a2a5518ab3ada000152392ad8233", "4b25a08a03013fe413e7e977feeca579b2d9e7b2243e85f89bd57d8592f8026d"),
    11: ("f09d495e146114216ee8a5c4b8c9c2bdf87aeaeb56c1eefa8a0ba640a96573a0", "6548f728b94f971768435a4a680af3cda3d79f6e7d4ffaa93f05dad242a3508f", "c8a85e416e1a335dae4a3097a3580c5f84ab1c42fe3cda1b15aaa54685a2a0a9"),
    12: ("87d6117bf54b2941e394383aab84a2debd62325209f8aab50409acf06ded8a97", "d499241517602d296b760543477853f1329eb23cd064eff000a0f1beb888a7f9", "9f280f44167b99a00d47b946de183ba7f6bd4e78d0bd7788ee0a07e3332898e8"),
    13: ("57d5d8a4d8b6e6e43c7f660a9ad565263565c3bc27f59cc6ed9f03e9c7e315db", "9b9ca606086d89cc642c4057bfb8fe141e89f2163cc6f950eb501eff71c1ba72", "f6f87e3e7da15e8e9d565d1b76d9112a8010d15e296ff7e0c2e2308fc9fac26e"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    require(path.is_file(), f"missing artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(artifact_prefix=None):
    here = Path(__file__).resolve().parent
    documentation = (here / "EXACT_LOCAL_REPAIR.md").read_text()
    for radius, hashes in CASES.items():
        require(all(documentation.count(value) == 1 for value in hashes),
                f"radius {radius}: hash table drift")
        transcript = here / "verification_logs" / f"r{radius}.drat-trim.log"
        require(transcript.read_text().splitlines().count("s VERIFIED") == 1,
                f"radius {radius}: transcript is not uniquely VERIFIED")
        if artifact_prefix is not None:
            prefix = Path(f"{artifact_prefix}-r{radius}")
            actual = (
                digest(Path(f"{prefix}.cnf")),
                digest(Path(f"{prefix}.drat")),
                digest(Path(f"{prefix}.drat-trim.log")),
            )
            require(actual == hashes, f"radius {radius}: artifact hash mismatch")
    print(f"LOCAL_EVIDENCE=PASS radii={len(CASES)} artifacts={'checked' if artifact_prefix else 'not-requested'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-prefix")
    args = parser.parse_args()
    verify(args.artifact_prefix)


if __name__ == "__main__":
    main()
